"""Bounded HTTP adapters. Discovery/probes are measurements, never permission or GPU evidence."""

import json
import re
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import httpx

from packages.ai.cloud_contracts import CloudPolicy
from packages.ai.contracts import Generation, Provider
from packages.ai.settings import Endpoint, secret_path


class ProviderFailure(RuntimeError):
    def __init__(self, code: str, *, retryable: bool = False, ambiguous: bool = False):
        super().__init__(code)
        self.code, self.retryable, self.ambiguous = code, retryable, ambiguous


@dataclass(frozen=True)
class Completion:
    content: str
    input_tokens: int | None
    output_tokens: int | None
    reasoning_channel_observed: bool = False


class InferenceProvider(Protocol):
    def close(self) -> None: ...
    def discover(self) -> list[dict[str, Any]]: ...
    def identity(self, name: str) -> dict[str, Any]: ...
    def probe(
        self, name: str, ceiling: int, *, progress: Callable[[str], None] | None = None
    ) -> dict[str, Any]: ...
    def body(
        self,
        name: str,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        parameters: Generation,
    ) -> dict[str, Any]: ...
    def complete(
        self,
        body: dict[str, Any],
        *,
        max_bytes: int,
        max_seconds: int,
        progress: Callable[[str], None],
    ) -> Completion: ...


class Adapter:
    def __init__(
        self,
        endpoint: Endpoint,
        provider: Provider,
        *,
        proxy: str | None = None,
        bearer_token: str | None = None,
        cloud_policy: CloudPolicy | None = None,
        secret_root: Path = Path("/run/secrets"),
    ):
        self.endpoint, self.provider = endpoint, provider
        self.cloud_policy = cloud_policy
        self._credential = bearer_token
        public = provider == "OPENROUTER"
        if public != (endpoint.transport == "OPENROUTER_PUBLIC"):
            raise ValueError("AI_PROVIDER_DESTINATION_MISMATCH")
        if public and (not proxy or not bearer_token or cloud_policy is None):
            raise ValueError("AI_CLOUD_PROXY_CREDENTIAL_AND_POLICY_REQUIRED")
        self.chat_path = "/api/v1/chat/completions" if public else "/v1/chat/completions"
        self.models_path = "/api/v1/models" if public else "/v1/models"
        tls = ssl.create_default_context(
            cafile=str(secret_path(endpoint.ca_file, secret_root)) if endpoint.ca_file else None
        )
        if endpoint.client_cert_file and endpoint.client_key_file:
            tls.load_cert_chain(
                secret_path(endpoint.client_cert_file, secret_root),
                secret_path(endpoint.client_key_file, secret_root),
            )
        headers = {"Accept": "application/json"}
        if endpoint.token_file:
            token = secret_path(endpoint.token_file, secret_root).read_text().strip()
            if not 16 <= len(token) <= 4096 or any(c.isspace() for c in token):
                raise ValueError("AI_CONNECTOR_SECRET_INVALID")
            headers["Authorization"] = "Bearer " + token
        if bearer_token is not None:
            if (
                not public
                or not 16 <= len(bearer_token) <= 4096
                or any(c.isspace() for c in bearer_token)
            ):
                raise ValueError("AI_CONNECTOR_SECRET_INVALID")
            headers["Authorization"] = "Bearer " + bearer_token
        self.client = httpx.Client(
            base_url="https://openrouter.ai" if public else endpoint.url.rstrip("/"),
            verify=tls,
            headers=headers,
            trust_env=False,
            follow_redirects=False,
            timeout=httpx.Timeout(10, connect=3),
            proxy=proxy
            if endpoint.transport in {"AUTHENTICATED_TLS", "OPENROUTER_PUBLIC"}
            else None,
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
        )

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def check(status: int) -> None:
        if status in {429, 503}:
            raise ProviderFailure("AI_PROVIDER_BUSY", retryable=True)
        if status >= 500:
            raise ProviderFailure("AI_PROVIDER_COMPLETION_UNKNOWN", ambiguous=True)
        if status != 200:
            raise ProviderFailure("AI_PROVIDER_REQUEST_REFUSED")

    def check_response(self, status: int) -> None:
        if self.provider == "OPENROUTER" and status in {401, 402, 403}:
            raise ProviderFailure(
                "AI_PROVIDER_CREDIT_REQUIRED" if status == 402 else "AI_PROVIDER_AUTH_REFUSED"
            )
        self.check(status)

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            with self.client.stream(method, path, json=body) as response:
                self.check_response(response.status_code)
                data = bytearray()
                for chunk in response.iter_bytes(8192):
                    data.extend(chunk)
                    if len(data) > (4 * 1024 * 1024 if self.provider == "OPENROUTER" else 262144):
                        raise ProviderFailure("AI_PROVIDER_METADATA_TOO_LARGE")
                if self._credential and self._credential.encode() in data:
                    raise ProviderFailure("AI_PROVIDER_SECRET_REFLECTION_REFUSED")
                result = json.loads(data)
                if not isinstance(result, dict):
                    raise ProviderFailure("AI_PROVIDER_METADATA_INVALID")
                return result
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise ProviderFailure("AI_PROVIDER_UNAVAILABLE", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderFailure("AI_PROVIDER_RESPONSE_UNKNOWN", ambiguous=True) from exc
        except (ValueError, UnicodeError) as exc:
            raise ProviderFailure("AI_PROVIDER_METADATA_INVALID") from exc

    def discover(self) -> list[dict[str, Any]]:
        native = self.provider not in {"PRIVATE_OPENAI", "OPENROUTER"}
        payload = self.request("GET", "/api/tags" if native else self.models_path)
        rows = payload.get("models" if native else "data", [])
        if not isinstance(rows, list) or len(rows) > (
            2000 if self.provider == "OPENROUTER" else 200
        ):
            raise ProviderFailure("AI_MODEL_LIST_INVALID")
        models: list[dict[str, Any]] = []
        for row in rows[:100] if self.provider == "OPENROUTER" else rows:
            if not isinstance(row, dict):
                continue
            name = row.get("name" if native else "id")
            if not isinstance(name, str) or len(name) > 150:
                continue
            # Local Ollama can route cloud aliases; a loopback address is not proof of privacy.
            if ":cloud" in name.lower() or row.get("remote_host") or row.get("remote_model"):
                continue
            models.append(
                {"name": name, "digest": row.get("digest"), "size_bytes": row.get("size")}
            )
        return models

    def identity(self, name: str) -> dict[str, Any]:
        if self.provider == "OPENROUTER":
            self.describe(name)
            return {"name": name, "digest": None}
        selected = next((m for m in self.discover() if m["name"] == name), None)
        if selected is None:
            raise ProviderFailure("AI_MODEL_NOT_AVAILABLE")
        return selected

    def describe(self, name: str) -> dict[str, Any]:
        if self.provider == "OPENROUTER":
            if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9][A-Za-z0-9_.:+-]{0,119}", name):
                raise ProviderFailure("AI_EXACT_MODEL_ID_REQUIRED")
            data = self.request("GET", self.models_path + "/" + name + "/endpoints").get("data", {})
            if not isinstance(data, dict) or data.get("id") != name or self.cloud_policy is None:
                raise ProviderFailure("AI_MODEL_NOT_AVAILABLE")
            endpoints = data.get("endpoints", [])
            selected = [
                r
                for r in endpoints
                if isinstance(r, dict) and r.get("tag") == self.cloud_policy.upstream_provider
            ]
            if not selected:
                raise ProviderFailure("AI_APPROVED_UPSTREAM_UNAVAILABLE")
            lengths = [r.get("context_length") for r in selected]
            if any(type(n) is not int or n < 1024 for n in lengths):
                raise ProviderFailure("AI_CONTEXT_LIMIT_UNKNOWN")
            return {"context_length": min(int(n) for n in lengths if n is not None)}
        self.identity(name)
        if self.provider not in {"PRIVATE_OPENAI", "OPENROUTER"}:
            result = self.request("POST", "/api/show", {"model": name})
        else:
            rows = self.request("GET", self.models_path).get("data", [])
            result = next((r for r in rows if isinstance(r, dict) and r.get("id") == name), {})
        if result.get("remote_model") or result.get("remote_host"):
            raise ProviderFailure("AI_CLOUD_ALIAS_REFUSED")
        return result

    def body(
        self,
        name: str,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        parameters: Generation,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"model": name, "messages": messages, "stream": True}
        if self.provider == "OLLAMA_NATIVE":
            body["format"] = schema
            body["options"] = {
                "num_ctx": parameters.context_tokens,
                "num_predict": parameters.output_tokens,
                "temperature": parameters.temperature,
                "top_p": parameters.top_p,
            }
            if parameters.seed is not None:
                body["options"]["seed"] = parameters.seed
            if parameters.reasoning == "DISABLED":
                body["think"] = False
        else:
            body.update(
                {
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "research_output",
                            "strict": True,
                            "schema": schema,
                        },
                    },
                    "max_tokens": parameters.output_tokens,
                    "temperature": parameters.temperature,
                    "top_p": parameters.top_p,
                }
            )
            if parameters.seed is not None or parameters.reasoning != "DEFAULT":
                raise ProviderFailure("AI_PARAMETER_CAPABILITY_UNVERIFIED")
        if self.provider == "OPENROUTER":
            if self.cloud_policy is None:
                raise ProviderFailure("AI_CLOUD_AUTHORIZATION_REQUIRED")
            body["provider"] = self.cloud_policy.routing()
            body["stream_options"] = {"include_usage": True}
        return body

    def complete(
        self,
        body: dict[str, Any],
        *,
        max_bytes: int,
        max_seconds: int,
        progress: Callable[[str], None],
    ) -> Completion:
        path = "/api/chat" if self.provider == "OLLAMA_NATIVE" else self.chat_path
        text, pending = "", b""
        total, input_tokens, output_tokens = 0, None, None
        done, reasoning_seen = False, False
        started = time.monotonic()
        try:
            with self.client.stream("POST", path, json=body) as response:
                self.check_response(response.status_code)
                for chunk in response.iter_bytes():
                    if time.monotonic() - started > max_seconds:
                        raise ProviderFailure("AI_PROVIDER_DEADLINE", ambiguous=True)
                    total += len(chunk)
                    if total > max_bytes * 8:
                        raise ProviderFailure("AI_PROVIDER_BODY_LIMIT")
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        if len(line) > max_bytes * 2:
                            raise ProviderFailure("AI_PROVIDER_LINE_LIMIT")
                        line = line.strip()
                        if not line or line.startswith(b":"):
                            continue
                        if line.startswith(b"data:"):
                            line = line[5:].strip()
                        elif self.provider != "OLLAMA_NATIVE":
                            continue  # SSE event/id/retry metadata carries no assistant content.
                        if line == b"[DONE]":
                            done = True
                            continue
                        event = json.loads(line)
                        if not isinstance(event, dict) or event.get("error"):
                            raise ProviderFailure("AI_PROVIDER_STREAM_INVALID")
                        if self.provider == "OLLAMA_NATIVE":
                            message = event.get("message", {})
                            reasoning_seen = reasoning_seen or bool(message.get("thinking"))
                            if message.get("tool_calls"):
                                raise ProviderFailure("AI_TOOL_SUGGESTION_REFUSED")
                            delta = message.get(
                                "content", ""
                            )  # Never read/persist message.thinking.
                            if event.get("done"):
                                done = True
                                input_tokens = event.get("prompt_eval_count")
                                output_tokens = event.get("eval_count")
                                if event.get("done_reason") == "length":
                                    raise ProviderFailure("AI_OUTPUT_TRUNCATED")
                        else:
                            choices = event.get("choices", [])
                            choice = choices[0] if choices else {}
                            message = choice.get("delta", {})
                            reasoning_seen = reasoning_seen or bool(
                                message.get("reasoning_content") or message.get("reasoning")
                            )
                            if message.get("tool_calls") or message.get("function_call"):
                                raise ProviderFailure("AI_TOOL_SUGGESTION_REFUSED")
                            delta = (
                                message.get("content") or ""
                            )  # Reasoning channels are intentionally ignored.
                            if choice.get("finish_reason") == "length":
                                raise ProviderFailure("AI_OUTPUT_TRUNCATED")
                            if choice.get("finish_reason") == "stop":
                                done = True
                            usage = event.get("usage") or {}
                            input_tokens = usage.get("prompt_tokens", input_tokens)
                            output_tokens = usage.get("completion_tokens", output_tokens)
                        if not isinstance(delta, str):
                            raise ProviderFailure("AI_PROVIDER_STREAM_INVALID")
                        text += delta
                        if len(text.encode()) > max_bytes:
                            raise ProviderFailure("AI_OUTPUT_BYTE_LIMIT")
                        if "<think" in text.lower() or "</think" in text.lower():
                            raise ProviderFailure("AI_REASONING_TRACE_REFUSED")
                        if self._credential and self._credential in text:
                            raise ProviderFailure("AI_PROVIDER_SECRET_REFLECTION_REFUSED")
                        progress("" if self.provider == "OPENROUTER" else text)
                    if len(pending) > max_bytes * 2:
                        raise ProviderFailure("AI_PROVIDER_LINE_LIMIT")
                if pending.strip() or not done:
                    raise ProviderFailure("AI_PROVIDER_INCOMPLETE", ambiguous=True)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise ProviderFailure("AI_PROVIDER_UNAVAILABLE", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderFailure("AI_PROVIDER_RESPONSE_UNKNOWN", ambiguous=True) from exc
        except (ValueError, TypeError, AttributeError, IndexError, UnicodeError) as exc:
            raise ProviderFailure("AI_PROVIDER_STREAM_INVALID") from exc
        for count in (input_tokens, output_tokens):
            if count is not None and (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
                or count > 1000000
            ):
                raise ProviderFailure("AI_PROVIDER_USAGE_INVALID")
        if (
            self.provider == "OPENROUTER"
            and output_tokens is not None
            and output_tokens > body.get("max_tokens", 0)
        ):
            raise ProviderFailure("AI_PROVIDER_OUTPUT_TOKEN_LIMIT")
        return Completion(text, input_tokens, output_tokens, reasoning_seen)

    def probe(
        self, name: str, ceiling: int, *, progress: Callable[[str], None] | None = None
    ) -> dict[str, Any]:
        identity, info = self.identity(name), self.describe(name)
        metadata = info.get("model_info", info)
        if not isinstance(metadata, dict):
            raise ProviderFailure("AI_PROVIDER_METADATA_INVALID")
        lengths = [
            v
            for k, v in metadata.items()
            if k.endswith("context_length") or k in {"max_model_len", "max_context_length"}
        ]
        limits = [
            n
            for n in lengths
            if isinstance(n, int) and not isinstance(n, bool) and 1024 <= n <= 10000000
        ]
        if not limits:
            raise ProviderFailure("AI_CONTEXT_LIMIT_UNKNOWN")
        limit = min(min(limits), ceiling, 32768)
        schema = {
            "type": "object",
            "properties": {"probe": {"type": "string", "enum": ["ok"]}},
            "required": ["probe"],
            "additionalProperties": False,
        }
        parameters = Generation(
            context_tokens=limit,
            output_tokens=64,
            seed=0 if self.provider == "OLLAMA_NATIVE" else None,
        )
        body = self.body(
            name, [{"role": "user", "content": 'Return only {"probe":"ok"}.'}], schema, parameters
        )
        result = self.complete(
            body,
            max_bytes=1024,
            max_seconds=90,
            progress=(lambda _: progress("") if progress else None),
        )
        if json.loads(result.content) != {"probe": "ok"}:
            raise ProviderFailure("AI_STRUCTURED_PROBE_FAILED")
        tool_status = (
            "UNVERIFIED_NOT_REQUESTED" if self.provider == "OPENROUTER" else self.probe_tools(name)
        )
        reasoning_status = "UNVERIFIED_CONTROL_SEMANTICS"
        if self.provider == "OLLAMA_NATIVE":
            try:
                disabled = self.body(
                    name,
                    [{"role": "user", "content": 'Return only {"probe":"ok"}.'}],
                    schema,
                    parameters.model_copy(update={"reasoning": "DISABLED"}),
                )
                observed = self.complete(
                    disabled,
                    max_bytes=1024,
                    max_seconds=90,
                    progress=(lambda _: progress("") if progress else None),
                )
                reasoning_status = (
                    "VERIFIED_DISABLED"
                    if not observed.reasoning_channel_observed
                    and json.loads(observed.content) == {"probe": "ok"}
                    else "UNSUPPORTED_REASONING_STILL_EMITTED"
                )
            except (ProviderFailure, ValueError):
                reasoning_status = "UNSUPPORTED_OR_REFUSED"
        elif self.provider != "OPENROUTER":
            # Probe vendor acceptance without inferring non-standard control semantics.
            try:
                self.request(
                    "POST",
                    "/v1/chat/completions",
                    {
                        "model": name,
                        "messages": [{"role": "user", "content": "Reply ok, without reasoning."}],
                        "max_tokens": 16,
                        "stream": False,
                        "reasoning_effort": "none",
                    },
                )
            except ProviderFailure:
                reasoning_status = "UNSUPPORTED_OR_REFUSED"
        advertised = info.get("capabilities", [])
        version = None
        if self.provider not in {"PRIVATE_OPENAI", "OPENROUTER"}:
            try:
                reported = self.request("GET", "/api/version").get("version")
                if isinstance(reported, str) and len(reported) <= 80 and reported.isprintable():
                    version = reported
            except ProviderFailure:
                pass  # A compatible proxy may omit version reporting; never invent it.
        quantization = (info.get("details") or {}).get("quantization_level")
        return {
            "provider_version": version,
            "quantization": quantization
            if isinstance(quantization, str) and len(quantization) <= 40
            else None,
            "structured_outputs": "VERIFIED",
            "streaming": "VERIFIED",
            "context_tokens": limit,
            "context_evidence": "PROVIDER_REPORTED_AND_BOUNDED_REQUEST_ACCEPTED",
            "tool_calling": tool_status,
            "reasoning_controls": reasoning_status,
            "seed_control": "VERIFIED_ACCEPTED"
            if self.provider == "OLLAMA_NATIVE"
            else "UNVERIFIED",
            "model_digest": identity.get("digest"),
            "model_name": name,
            "advertised_capabilities": [c[:32] for c in advertised[:16] if isinstance(c, str)]
            if isinstance(advertised, list)
            else [],
            "probe_usage": {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            },
            "gpu_availability": "UNKNOWN",
        }

    def probe_tools(self, name: str) -> str:
        tool = {
            "type": "function",
            "function": {
                "name": "capability_probe",
                "description": "Return the fixed nonce only; no operation is performed.",
                "parameters": {
                    "type": "object",
                    "properties": {"nonce": {"type": "string", "enum": ["probe-only"]}},
                    "required": ["nonce"],
                    "additionalProperties": False,
                },
            },
        }
        payload: dict[str, Any] = {
            "model": name,
            "messages": [
                {
                    "role": "user",
                    "content": "Suggest capability_probe, nonce probe-only. Nothing will execute.",
                }
            ],
            "tools": [tool],
            "stream": False,
        }
        if self.provider == "OLLAMA_NATIVE":
            payload["options"] = {"num_predict": 128}
            path = "/api/chat"
        else:
            payload.update(
                {
                    "max_tokens": 128,
                    "tool_choice": {"type": "function", "function": {"name": "capability_probe"}},
                }
            )
            path = "/v1/chat/completions"
        try:
            response = self.request("POST", path, payload)
            message = (
                response.get("message", {})
                if self.provider == "OLLAMA_NATIVE"
                else response.get("choices", [{}])[0].get("message", {})
            )
            calls = message.get("tool_calls", [])
            if len(calls) != 1:
                return "UNSUPPORTED_OR_NOT_OBSERVED"
            function = calls[0].get("function", {})
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if function.get("name") == "capability_probe" and arguments == {"nonce": "probe-only"}:
                return "VERIFIED_INERT_SUGGESTIONS_ONLY"
        except (ProviderFailure, ValueError, TypeError, AttributeError, IndexError):
            return "UNSUPPORTED_OR_REFUSED"
        return "UNSUPPORTED_OR_NOT_OBSERVED"


def create_provider(
    endpoint: Endpoint,
    provider: Provider,
    *,
    proxy: str | None,
    secret_root: Path,
    bearer_token: str | None = None,
    cloud_policy: CloudPolicy | None = None,
) -> InferenceProvider:
    # Trusted registry only; future adapters implement the protocol, never user module imports.
    adapters = {
        "OLLAMA_NATIVE": Adapter,
        "OLLAMA_OPENAI": Adapter,
        "PRIVATE_OPENAI": Adapter,
        "OPENROUTER": Adapter,
    }
    return adapters[provider](
        endpoint,
        provider,
        proxy=proxy,
        secret_root=secret_root,
        bearer_token=bearer_token,
        cloud_policy=cloud_policy,
    )
