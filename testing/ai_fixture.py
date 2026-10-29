"""Real loopback HTTP protocol fixture, not a model or evidence of inference quality."""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

NAME = "SYNTHETIC_HTTP_FIXTURE:1"
DIGEST = "synthetic-http-fixture-v1"


def structured(properties: dict[str, Any]) -> dict[str, Any]:
    common: dict[str, Any] = {
        "schema_version": 1,
        "evidence_refs": [],
        "missing_evidence": {"items": ["Fixture only; no financial evidence."]},
    }
    if "probe" in properties:
        return {"probe": "ok"}
    if "hypothesis" in properties:
        return {
            **common,
            "title": "Ipoteză sintetică",
            "hypothesis": "Necesită testare istorică.",
            "test_plan": ["Verifică datele și costurile."],
            "verified": False,
        }
    if "candidate_source" in properties:
        return {
            **common,
            "summary": "Text de test, neexecutabil",
            "language": "text",
            "candidate_source": "No executable strategy.",
            "suggested_tests": ["Review only."],
            "executable": False,
        }
    if "objections" in properties:
        return {
            **common,
            "summary": "Critică sintetică",
            "objections": ["Lipsește dovada."],
            "certifies_strategy": False,
        }
    return {
        **common,
        "summary": "Rezumat sintetic; nu este o concluzie financiară.",
        "verified": False,
    }


class Fixture(ThreadingHTTPServer):
    daemon_threads = True
    behavior = "normal"
    seen = 0
    expected_authorization: str | None = None
    entered: threading.Event
    release: threading.Event

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), Handler)
        self.entered, self.release = threading.Event(), threading.Event()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    server: Fixture
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Never log request bodies, authorization or model output.

    def reply(
        self, payload: Any, status: int = 200, content_type: str = "application/json"
    ) -> None:
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        with suppress(BrokenPipeError, ConnectionResetError):
            self.wfile.write(data)

    def do_GET(self) -> None:
        if (
            self.server.expected_authorization
            and self.headers.get("Authorization") != self.server.expected_authorization
        ):
            self.reply({}, 401)
            return
        metadata = {"name": NAME, "id": NAME, "digest": DIGEST, "max_model_len": 8192}
        if self.path in {"/api/tags", "/v1/models"}:
            self.reply({"models" if self.path == "/api/tags" else "data": [metadata]})
        elif self.path == "/api/version":
            self.reply({"version": "SYNTHETIC_HTTP_FIXTURE"})
        else:
            self.reply({}, 404)

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= 100000:
            self.reply({}, 413)
            return
        body = json.loads(self.rfile.read(size))
        if self.path == "/api/show":
            self.reply(
                {
                    "model_info": {"fixture.context_length": 8192},
                    "capabilities": ["completion", "tools", "thinking"],
                }
            )
            return
        if self.path not in {"/api/chat", "/v1/chat/completions"}:
            self.reply({}, 404)
            return
        native = self.path == "/api/chat"
        if not body.get("stream"):
            message: dict[str, Any] = {"content": "ok"}
            if body.get("tools"):
                message["tool_calls"] = [
                    {"function": {"name": "capability_probe", "arguments": {"nonce": "probe-only"}}}
                ]
            self.reply({"message": message} if native else {"choices": [{"message": message}]})
            return
        self.server.seen += 1
        if self.server.behavior in {"busy", "unknown"}:
            self.reply({}, 429 if self.server.behavior == "busy" else 500)
            return
        schema = body.get("format") if native else body["response_format"]["json_schema"]["schema"]
        output = structured(schema.get("properties", {}))
        if self.server.behavior == "invalid":
            output["unexpected_authority"] = True
        if self.server.behavior == "invented":
            output["evidence_refs"] = ["dataset:never-authorized"]
        raw = json.dumps(output, ensure_ascii=False)
        chunks = [raw[: len(raw) // 2], raw[len(raw) // 2 :]]
        events = []
        for index, chunk in enumerate(chunks):
            if native:
                message = {"content": chunk}
                if body.get("think") is not False:
                    message["thinking"] = "PRIVATE_REASONING_MUST_NOT_PERSIST"
                if self.server.behavior == "tool":
                    message["tool_calls"] = [{"function": {"name": "unsafe"}}]
                event = {
                    "message": message,
                    "done": index == 1,
                    "prompt_eval_count": 30,
                    "eval_count": 40,
                }
                events.append(json.dumps(event).encode() + b"\n")
            else:
                delta: dict[str, Any] = {"content": chunk, "reasoning_content": "PRIVATE_REASONING"}
                if self.server.behavior == "tool":
                    delta["tool_calls"] = [{"function": {"name": "unsafe"}}]
                event = {
                    "choices": [{"delta": delta, "finish_reason": "stop" if index == 1 else None}],
                    "usage": {"prompt_tokens": 30, "completion_tokens": 40},
                }
                events.append(b"data: " + json.dumps(event).encode() + b"\n\n")
        if self.server.behavior == "incomplete":
            events = events[:1]
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson" if native else "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(events[0])
            self.wfile.flush()
            self.server.entered.set()
            if self.server.behavior == "blocked":
                self.server.release.wait(
                    8
                )  # Test-controlled barrier, never application synchronization.
            for data in events[1:]:
                self.wfile.write(data)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


@contextmanager
def running_fixture() -> Iterator[Fixture]:
    server = Fixture()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.release.set()
        server.shutdown()
        server.server_close()
        thread.join(3)
