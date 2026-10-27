"""Protocol/SDK-compatible fixtures are MOCKED contracts, not broker connectivity evidence."""

import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from pydantic import SecretStr
from test_execution_engine import initial

from packages.brokers.contracts import BrokerAdapter, ExternalExecutionDenied, SnapshotRequest
from packages.execution.adapter import SimulatorAdapter
from services.broker_bridge.app import BridgeConfig, create_bridge
from services.broker_bridge.ctrader import (
    CTraderAdapter,
    JsonProtocol,
    ProtocolFailure,
    decimal_units,
)
from services.broker_bridge.mt5 import MT5Adapter
from services.broker_bridge.security import OAuth, Tokens, TokenVault, private_file


class TerminalFixture:
    contract_fixture = True

    def initialize(self, timeout: int) -> bool:
        return timeout == 10000

    def shutdown(self) -> None:
        self.closed = True

    def terminal_info(self) -> Any:
        return SimpleNamespace(connected=True, tradeapi_disabled=True)

    def account_info(self) -> Any:
        return SimpleNamespace(
            login=123,
            server="fixture-demo",
            trade_mode=0,
            trade_allowed=False,
            margin_mode=2,
            currency="USD",
            balance=1000.25,
            equity=1000.25,
        )

    def orders_get(self) -> tuple[()]:
        return ()

    def positions_get(self) -> tuple[()]:
        return ()

    def history_deals_get(self, start: datetime, end: datetime) -> tuple[()]:
        assert end > start
        return ()


class ChannelFixture:
    def __init__(self, scope: object = 0, live: object = False) -> None:
        self.scope, self.live = scope, live
        self.sent: list[dict[str, Any]] = []
        self.replies: list[str] = []

    def send(self, message: str) -> None:
        request = json.loads(message)
        self.sent.append(request)
        kind = request["payloadType"]
        payload = request["payload"]
        response: dict[str, Any] = (
            {"ctidTraderAccountId": 123} if "ctidTraderAccountId" in payload else {}
        )
        if kind == 2149:
            response.update(
                permissionScope=self.scope,
                ctidTraderAccount=[{"ctidTraderAccountId": 123, "isLive": self.live}],
            )
        elif kind == 2121:
            response["trader"] = {
                "ctidTraderAccountId": 123,
                "balance": 100025,
                "moneyDigits": 2,
                "depositAssetId": 1,
                "accountType": 0,
            }
        elif kind == 2112:
            response["asset"] = [{"assetId": 1, "name": "USD"}]
        elif kind == 2114:
            response["symbol"] = [{"symbolId": 1, "symbolName": "EURUSD.fixture"}]
        elif kind == 2116:
            response["symbol"] = [
                {
                    "symbolId": 1,
                    "digits": 5,
                    "minVolume": 1000,
                    "maxVolume": 100000,
                    "stepVolume": 1000,
                    "lotSize": 10000000,
                }
            ]
        elif kind == 2127:
            at = datetime.now(UTC)
            self.replies.append(
                json.dumps(
                    {
                        "payloadType": 2131,
                        "payload": {
                            "ctidTraderAccountId": 123,
                            "symbolId": 1,
                            "bid": 110000,
                            "ask": 110002,
                            "timestamp": int(at.timestamp() * 1000),
                        },
                    }
                )
            )
        elif kind == 2124:
            response.update(order=[], position=[])
        elif kind == 2133:
            response.update(deal=[], hasMore=False)
        self.replies.append(
            json.dumps(
                {
                    "payloadType": kind + 1,
                    "clientMsgId": request["clientMsgId"],
                    "payload": response,
                }
            )
        )

    def recv(self, timeout: float | None = None) -> str:
        if not self.replies:
            raise TimeoutError
        return self.replies.pop(0)


def test_all_adapters_conform_to_read_contract_and_external_mutations_deny() -> None:
    mt5: BrokerAdapter = MT5Adapter(True, TerminalFixture())
    ctrader: BrokerAdapter = CTraderAdapter(
        "fixture", "fixture-secret", "fixture-access", True, JsonProtocol(ChannelFixture())
    )
    simulator: BrokerAdapter = SimulatorAdapter(initial(), "synthetic-account")
    for adapter, request in (
        (mt5, SnapshotRequest(account_id="123", server="fixture-demo", source_sequence=0)),
        (
            ctrader,
            SnapshotRequest(account_id="123", server="demo.ctraderapi.com", source_sequence=0),
        ),
        (
            simulator,
            SnapshotRequest(
                account_id="synthetic-account", server="SYNTHETIC_BROKER", source_sequence=0
            ),
        ),
    ):
        observed = adapter.snapshot(request)
        assert (
            observed.account_id == request.account_id
            and observed.external_execution_enabled is False
        )
        assert observed.source in {"CONTRACT_FIXTURE", "SIMULATED"}
        for method in (adapter.cancel, adapter.modify):
            with pytest.raises(ExternalExecutionDenied):
                method("order-id")
        with pytest.raises(ExternalExecutionDenied):
            adapter.submit(None)  # type: ignore[arg-type]


@pytest.mark.parametrize("scope", [1, "SCOPE_TRADE", None, True, False, 0.0])
def test_ctrader_rejects_trade_or_unverified_permission_scope(scope: object) -> None:
    fixture = ChannelFixture(scope=scope)
    adapter = CTraderAdapter(
        "fixture", "fixture-secret", "fixture-access", True, JsonProtocol(fixture)
    )
    with pytest.raises(PermissionError, match="VIEW_ONLY"):
        adapter.snapshot(
            SnapshotRequest(account_id="123", server="demo.ctraderapi.com", source_sequence=0)
        )
    assert [packet["payloadType"] for packet in fixture.sent] == [2100, 2149]


@pytest.mark.parametrize("live", [True, None, 0])
def test_ctrader_refuses_live_or_missing_demo_identity(live: object) -> None:
    adapter = CTraderAdapter(
        "fixture", "fixture-secret", "fixture-access", True, JsonProtocol(ChannelFixture(live=live))
    )
    with pytest.raises(PermissionError, match="DEMO_ACCOUNT"):
        adapter.snapshot(
            SnapshotRequest(account_id="123", server="demo.ctraderapi.com", source_sequence=0)
        )


@pytest.mark.parametrize("kind", [2106, 2108, 2109, 2110, 2111, 2170])
def test_ctrader_write_messages_cannot_reach_transport(kind: int) -> None:
    channel = ChannelFixture()
    with pytest.raises(PermissionError):
        JsonProtocol(channel).send(kind, {}, "fixture-message")
    assert not channel.sent


def test_protocol_malformed_revoked_duplicate_and_out_of_order_replies() -> None:
    channel = ChannelFixture()
    protocol = JsonProtocol(channel)
    channel.replies = ["not-json"]
    with pytest.raises(ProtocolFailure, match="MALFORMED"):
        protocol.receive()
    channel.replies = [json.dumps({"payloadType": 2147, "payload": {}})]
    with pytest.raises(PermissionError, match="REVOKED"):
        protocol.receive()
    channel.replies = [
        json.dumps({"payloadType": 2101, "clientMsgId": "old-reply", "payload": {}})
    ] * 2
    assert protocol.request(2100, {"clientId": "fixture"}).payloadType == 2101
    assert list(protocol.seen) == ["old-reply:2101"]


def test_ctrader_actual_protocol_units_and_two_sided_spot_fixture() -> None:
    from decimal import Decimal

    channel = ChannelFixture()
    adapter = CTraderAdapter(
        "fixture", "fixture-secret", "fixture-access", True, JsonProtocol(channel)
    )
    snapshot = adapter.snapshot(
        SnapshotRequest(
            account_id="123",
            server="demo.ctraderapi.com",
            source_sequence=1,
            symbols=["EURUSD.fixture"],
        )
    )
    assert snapshot.balance == Decimal("1000.25")
    assert snapshot.quotes[0].bid == Decimal("1.10000")
    assert snapshot.quotes[0].ask == Decimal("1.10002")
    assert snapshot.symbols[0].min_volume == Decimal("10")
    assert snapshot.symbols[0].contract_size is None
    for bad in (True, 1.2, "0.5", "1e3"):
        with pytest.raises(ProtocolFailure, match="INTEGER_UNITS"):
            decimal_units(bad)


def test_oauth_exchange_refresh_and_one_use_callback_are_mocked_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx

    tmp_path.chmod(0o700)
    key_path = tmp_path / "key"
    key_path.write_bytes(Fernet.generate_key())
    key_path.chmod(0o600)
    vault = TokenVault(tmp_path / "vault.enc", key_path)
    client_secret = secrets.token_urlsafe(32)
    access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    calls: list[str] = []

    def response(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "openapi.ctrader.com" and request.url.path == "/apps/token"
        assert request.url.params["client_secret"] == client_secret
        calls.append(request.url.params["grant_type"])
        return httpx.Response(
            200,
            json={
                "accessToken": access,
                "refreshToken": refresh,
                "expiresIn": 3600,
                "errorCode": None,
            },
        )

    original_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original_client(transport=httpx.MockTransport(response), **kwargs),
    )
    oauth = OAuth(
        "fixture-client", SecretStr(client_secret), "https://127.0.0.1:18443/oauth/callback", vault
    )
    state = parse_qs(urlsplit(oauth.start()).query)["state"][0]
    oauth.callback("fixture-code", state)
    assert vault.read().access.get_secret_value() == access
    with pytest.raises(PermissionError):
        oauth.callback("fixture-code", state)
    vault.write(
        Tokens(
            access=SecretStr("expired-fixture"),
            refresh=SecretStr(refresh),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    assert oauth.current().access.get_secret_value() == access
    assert calls == ["authorization_code", "refresh_token"]


@pytest.mark.parametrize(
    ("field", "value"),
    [("trade_mode", 2), ("trade_allowed", True), ("login", 999), ("server", "live-server")],
)
def test_mt5_demo_investor_identity_is_mandatory(field: str, value: object) -> None:
    sdk = TerminalFixture()
    account = sdk.account_info()
    setattr(account, field, value)
    sdk.account_info = lambda: account  # type: ignore[method-assign]
    with pytest.raises(PermissionError):
        MT5Adapter(True, sdk).snapshot(
            SnapshotRequest(account_id="123", server="fixture-demo", source_sequence=0)
        )
    assert sdk.closed


def test_private_token_vault_encryption_and_oauth_state_scope(tmp_path: Path) -> None:
    tmp_path.chmod(0o700)
    key_path = tmp_path / "vault.key"
    key_path.write_bytes(Fernet.generate_key())
    key_path.chmod(0o600)
    vault = TokenVault(tmp_path / "tokens.enc", key_path)
    access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    tokens = Tokens(
        access=SecretStr(access),
        refresh=SecretStr(refresh),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    vault.write(tokens)
    assert (
        access.encode() not in private_file(vault.path)
        and vault.read().access.get_secret_value() == access
    )
    oauth = OAuth(
        "fixture-client",
        SecretStr(secrets.token_urlsafe(32)),
        "https://127.0.0.1:18443/oauth/callback",
        vault,
    )
    query = parse_qs(urlsplit(oauth.start()).query)
    assert query["scope"] == ["accounts"] and len(query["state"][0]) >= 43
    with pytest.raises(PermissionError, match="state"):
        oauth.callback("fixture-code", "wrong-state")
    key_path.chmod(0o644)
    with pytest.raises(PermissionError, match="owner-only"):
        private_file(key_path)


def test_private_bridge_requires_service_identity_and_signs_only_pinned_snapshots(
    tmp_path: Path,
) -> None:
    token = secrets.token_urlsafe(32)
    signing = Ed25519PrivateKey.generate()
    token_path, signing_path = tmp_path / "auth.txt", tmp_path / "signing.key"
    token_path.write_text(token)
    signing_path.write_bytes(signing.private_bytes_raw())
    token_path.chmod(0o600)
    signing_path.chmod(0o600)
    config = BridgeConfig(
        provider="MT5",
        authorized_demo_reads=True,
        connection_id=uuid4(),
        account_id="123",
        server="fixture-demo",
        authorization_token_file=token_path,
        signing_key_file=signing_path,
        tls_cert=tmp_path / "server.pem",
        tls_key=tmp_path / "server.key",
        client_ca=tmp_path / "ca.pem",
    )
    adapter = MT5Adapter(True, TerminalFixture())
    client = TestClient(create_bridge(config, adapter.snapshot))
    assert client.get("/health").status_code == 403
    client.headers.update({"Authorization": "Bearer " + token})
    assert client.get("/health").json()["external_execution"] is False
    request = {"account_id": "123", "server": "fixture-demo", "source_sequence": 0}
    response = client.post("/snapshot", json=request)
    assert response.status_code == 200
    data = response.json()
    signature = bytes.fromhex(data.pop("signature"))
    signing.public_key().verify(
        signature,
        json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(),
    )
    assert response.json()["snapshot"]["source"] == "CONTRACT_FIXTURE"
    assert client.post("/snapshot", json={**request, "account_id": "other"}).status_code == 403
    for path in ("/orders", "/cancel", "/modify"):
        assert client.post(path, json={}).status_code == 404
