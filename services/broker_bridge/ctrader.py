"""Official Open API JSON messages over demo-only TLS WebSocket, with a read allowlist."""

import json
import re
import ssl
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictInt
from websockets.sync.client import connect

from packages.brokers.contracts import (
    BrokerSnapshot,
    BrokerSymbol,
    ObservedOrder,
    ReadOnlyAdapter,
    SnapshotRequest,
)
from packages.execution.contracts import Quote

DEMO_URL = "wss://demo.ctraderapi.com:5036"
READ_REQUESTS = {51, 2100, 2102, 2112, 2114, 2116, 2121, 2124, 2127, 2129, 2133, 2149}
EVENTS = {51, 2120, 2123, 2126, 2131, 2147, 2148, 2164}
RESPONSES = {2101, 2103, 2113, 2115, 2117, 2122, 2125, 2128, 2130, 2134, 2150}


class ProtocolFailure(ConnectionError):
    pass


class Envelope(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    payloadType: StrictInt
    clientMsgId: str | None = Field(default=None, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class Channel(Protocol):
    def send(self, message: str) -> None: ...
    def recv(self, timeout: float | None = None) -> str | bytes: ...


class JsonProtocol:
    def __init__(self, channel: Channel) -> None:
        self.channel = channel
        self.events: deque[Envelope] = deque(maxlen=1000)
        self.seen: deque[str] = deque(maxlen=2048)
        self.last_sent: deque[float] = deque(maxlen=10)
        self.last_history = 0.0
        self.last_heartbeat = time.monotonic()

    def send(self, kind: int, payload: dict[str, Any], identifier: str) -> None:
        if kind not in READ_REQUESTS:
            raise PermissionError("CTRADER_EXTERNAL_ORDER_MESSAGE_DENIED")
        now = time.monotonic()
        if len(self.last_sent) == 10 and now - self.last_sent[0] < 1:
            time.sleep(1 - (now - self.last_sent[0]))
        if kind == 2133 and now - self.last_history < 1:
            time.sleep(1 - (now - self.last_history))
        self.channel.send(
            json.dumps({"clientMsgId": identifier, "payloadType": kind, "payload": payload})
        )
        self.last_sent.append(time.monotonic())
        if kind == 2133:
            self.last_history = time.monotonic()

    def receive(self) -> Envelope:
        try:
            message = self.channel.recv(timeout=2)
            if len(message) > 1024 * 1024:
                raise ProtocolFailure("CTRADER_MESSAGE_LIMIT")
            envelope = Envelope.model_validate_json(message)
        except TimeoutError:
            if time.monotonic() - self.last_heartbeat >= 10:
                self.send(51, {}, str(uuid4()))
                self.last_heartbeat = time.monotonic()
            raise
        except (ValueError, TypeError) as error:
            raise ProtocolFailure("CTRADER_MALFORMED_MESSAGE") from error
        if envelope.payloadType in {2147, 2148, 2164}:
            raise PermissionError("CTRADER_AUTH_REVOKED_REAUTHORIZE")
        if envelope.payloadType == 2142:
            raise ProtocolFailure("CTRADER_REQUEST_FAILED")
        if envelope.payloadType not in RESPONSES | EVENTS:
            raise ProtocolFailure("CTRADER_UNKNOWN_MESSAGE_TYPE")
        return envelope

    def request(self, kind: int, payload: dict[str, Any]) -> Envelope:
        identifier = str(uuid4())
        self.send(kind, payload, identifier)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                envelope = self.receive()
            except TimeoutError:
                continue
            if envelope.payloadType in EVENTS:
                if len(self.events) == self.events.maxlen:
                    raise ProtocolFailure("CTRADER_EVENT_BUFFER_OVERFLOW_RECONCILE")
                self.events.append(envelope)
            elif envelope.clientMsgId == identifier:
                if envelope.payloadType != kind + 1:
                    raise ProtocolFailure("CTRADER_RESPONSE_CORRELATION_MISMATCH")
                if "ctidTraderAccountId" in payload and str(
                    envelope.payload.get("ctidTraderAccountId")
                ) != str(payload["ctidTraderAccountId"]):
                    raise ProtocolFailure("CTRADER_RESPONSE_ACCOUNT_MISMATCH")
                return envelope
            else:
                # Never attribute a late/duplicate unrelated reply to the current request.
                key = str(envelope.clientMsgId) + ":" + str(envelope.payloadType)
                if key not in self.seen:
                    self.seen.append(key)
        raise ProtocolFailure("CTRADER_RESPONSE_TIMEOUT_NO_EXECUTION_RETRY")


def decimal_units(value: object, divisor: int = 100) -> Decimal:
    if not (
        (type(value) is int) or (isinstance(value, str) and re.fullmatch(r"-?[0-9]{1,19}", value))
    ):
        raise ProtocolFailure("CTRADER_INEXACT_INTEGER_UNITS")
    return Decimal(str(value)) / divisor


class CTraderAdapter(ReadOnlyAdapter):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        authorized_demo: bool,
        protocol: JsonProtocol | None = None,
    ) -> None:
        if not authorized_demo:
            raise PermissionError("Explicit demo read authorization required")
        self.client_id, self.client_secret, self.access_token = (
            client_id,
            client_secret,
            access_token,
        )
        self.fixture_protocol = protocol

    def snapshot(self, request: SnapshotRequest) -> BrokerSnapshot:
        if self.fixture_protocol:
            return self.read(self.fixture_protocol, request, True)
        # Fixed host, validated TLS, no proxy or redirect route to a live endpoint.
        for attempt in range(3):
            try:
                with connect(
                    DEMO_URL,
                    ssl=ssl.create_default_context(),
                    proxy=None,
                    open_timeout=10,
                    close_timeout=3,
                    max_size=1048576,
                    max_queue=16,
                ) as channel:
                    result = self.read(JsonProtocol(channel), request, False)
                    result.reconnect_attempt = attempt
                    return result
            except PermissionError:
                raise
            except (OSError, ConnectionError, TimeoutError):
                if attempt == 2:
                    raise ProtocolFailure("CTRADER_BOUNDED_RECONNECT_EXHAUSTED") from None
                time.sleep(2**attempt)
        raise ProtocolFailure("CTRADER_UNAVAILABLE")

    def read(
        self, protocol: JsonProtocol, request: SnapshotRequest, fixture: bool
    ) -> BrokerSnapshot:
        protocol.request(2100, {"clientId": self.client_id, "clientSecret": self.client_secret})
        discovery = protocol.request(2149, {"accessToken": self.access_token}).payload
        permission = discovery.get("permissionScope")
        if not (
            (type(permission) is int and permission == 0)
            or (isinstance(permission, str) and permission == "SCOPE_VIEW")
        ):
            raise PermissionError("CTRADER_VERIFIED_VIEW_ONLY_TOKEN_REQUIRED")
        accounts = discovery.get("ctidTraderAccount", [])
        selected = [a for a in accounts if str(a.get("ctidTraderAccountId")) == request.account_id]
        if len(selected) != 1 or selected[0].get("isLive") is not False:
            raise PermissionError("CTRADER_PINNED_DEMO_ACCOUNT_REQUIRED")
        if request.server != "demo.ctraderapi.com":
            raise PermissionError("CTRADER_DEMO_ENDPOINT_IDENTITY_REQUIRED")
        account_id = int(request.account_id)
        scope = {"ctidTraderAccountId": account_id}
        protocol.request(2102, {**scope, "accessToken": self.access_token})
        trader = protocol.request(2121, scope).payload["trader"]
        if str(trader.get("ctidTraderAccountId")) != request.account_id:
            raise ProtocolFailure("CTRADER_TRADER_ID_MISMATCH")
        assets = protocol.request(2112, scope).payload.get("asset", [])
        currencies = {str(a["assetId"]): str(a["name"]) for a in assets}
        currency = currencies.get(str(trader.get("depositAssetId")))
        digits = trader.get("moneyDigits")
        if (
            not currency
            or not isinstance(digits, int)
            or isinstance(digits, bool)
            or not 0 <= digits <= 12
        ):
            raise ProtocolFailure("CTRADER_ACCOUNT_MONEY_SPEC_MISSING")
        light = protocol.request(2114, scope).payload.get("symbol", [])
        chosen = [s for s in light if s.get("symbolName") in request.symbols]
        if len(chosen) != len(request.symbols):
            raise ProtocolFailure("CTRADER_REQUESTED_SYMBOL_MISSING")
        ids = [int(s["symbolId"]) for s in chosen]
        details = (
            protocol.request(2116, {**scope, "symbolId": ids}).payload.get("symbol", [])
            if ids
            else []
        )
        names = {int(s["symbolId"]): str(s["symbolName"]) for s in chosen}
        observed = datetime.now(UTC)
        symbols: list[BrokerSymbol] = []
        for info in details:
            identifier = int(info["symbolId"])
            if identifier not in names:
                raise ProtocolFailure("CTRADER_SYMBOL_ID_MISMATCH")
            symbols.append(
                BrokerSymbol(
                    broker_symbol=names[identifier],
                    symbol_id=str(identifier),
                    digits=info.get("digits"),
                    observed_at=observed,
                    source="CTRADER_OPEN_API",
                    min_volume=decimal_units(info["minVolume"]) if "minVolume" in info else None,
                    max_volume=decimal_units(info["maxVolume"]) if "maxVolume" in info else None,
                    volume_step=decimal_units(info["stepVolume"]) if "stepVolume" in info else None,
                    account_currency=currency,
                    sessions=info.get("schedule", []),
                    metadata={
                        k: v
                        for k, v in info.items()
                        if k
                        in {
                            "lotSize",
                            "slDistance",
                            "tpDistance",
                            "distanceSetIn",
                            "scheduleTimeZone",
                            "tradingMode",
                            "holiday",
                            "leverageId",
                            "swapLong",
                            "swapShort",
                            "swapCalculationType",
                        }
                    },
                )
            )
        reconcile = protocol.request(2124, scope).payload
        if str(reconcile.get("ctidTraderAccountId")) != request.account_id:
            raise ProtocolFailure("CTRADER_RECONCILIATION_ACCOUNT_MISMATCH")
        history = protocol.request(
            2133,
            {
                **scope,
                "fromTimestamp": int((observed - timedelta(days=request.history_days)).timestamp())
                * 1000,
                "toTimestamp": int(observed.timestamp()) * 1000,
                "maxRows": 500,
            },
        ).payload
        if ids:
            protocol.request(2127, {**scope, "symbolId": ids, "subscribeToSpotTimestamp": True})
        quotes: dict[int, Quote] = {}
        deadline = time.monotonic() + 10
        while len(quotes) < len(ids) and time.monotonic() < deadline:
            if protocol.events:
                message = protocol.events.popleft()
            else:
                try:
                    message = protocol.receive()
                except TimeoutError:
                    continue
            if message.payloadType != 2131:
                continue
            raw = message.payload
            if str(raw.get("ctidTraderAccountId")) != request.account_id:
                raise ProtocolFailure("CTRADER_QUOTE_ACCOUNT_MISMATCH")
            identifier = int(raw["symbolId"])
            if identifier not in names:
                raise ProtocolFailure("CTRADER_UNSUBSCRIBED_SYMBOL")
            if not all(k in raw for k in ("bid", "ask", "timestamp")):
                # Never combine a fresh side with an undated/stale opposite side.
                continue
            millis = int(raw["timestamp"])
            at = datetime.fromtimestamp(millis // 1000, UTC) + timedelta(milliseconds=millis % 1000)
            quote = Quote(
                symbol=names[identifier],
                event_time=at,
                available_at=datetime.now(UTC),
                sequence=request.source_sequence,
                bid=decimal_units(raw["bid"], 100000),
                ask=decimal_units(raw["ask"], 100000),
            )
            if identifier in quotes and quote.event_time < quotes[identifier].event_time:
                raise ProtocolFailure("CTRADER_OUT_OF_ORDER_SPOT")
            quotes[identifier] = quote
        if len(quotes) != len(ids):
            raise ProtocolFailure("CTRADER_FRESH_TWO_SIDED_QUOTES_UNAVAILABLE")

        def records(rows: list[dict[str, Any]], kind: str) -> list[ObservedOrder]:
            if len(rows) > 500:
                raise ProtocolFailure("CTRADER_RECONCILIATION_LIMIT")
            output = []
            for row in rows:
                trade = row.get("tradeData", row)
                if str(row.get("ctidTraderAccountId", account_id)) != request.account_id:
                    raise ProtocolFailure("CTRADER_ROW_ACCOUNT_MISMATCH")
                symbol_id = int(trade["symbolId"])
                # Account positions can include symbols outside the requested quote subset.
                symbol = next(
                    (str(s["symbolName"]) for s in light if int(s["symbolId"]) == symbol_id), None
                )
                if symbol is None:
                    raise ProtocolFailure("CTRADER_POSITION_SYMBOL_UNKNOWN")
                output.append(
                    ObservedOrder(
                        broker_id=str(row[kind + "Id"]),
                        symbol=symbol,
                        side=str(trade["tradeSide"]),
                        state=str(row.get(kind + "Status", "BROKER_REPORTED")),
                        volume=decimal_units(trade["volume"]),
                        price=Decimal(str(row["price"])) if "price" in row else None,
                        stop_loss=Decimal(str(row["stopLoss"])) if "stopLoss" in row else None,
                        take_profit=Decimal(str(row["takeProfit"]))
                        if "takeProfit" in row
                        else None,
                        observed_at=datetime.now(UTC),
                        source_sequence=request.source_sequence,
                    )
                )
            return output

        return BrokerSnapshot(
            provider="CTRADER",
            environment="DEMO_READ_ONLY",
            account_id=request.account_id,
            server=request.server,
            currency=currency,
            account_mode="HEDGING"
            if trader.get("accountType") in (0, "HEDGED")
            else "NETTING"
            if trader.get("accountType") in (1, "NETTED")
            else None,
            balance=decimal_units(trader["balance"], 10**digits),
            equity=None,
            observed_at=datetime.now(UTC),
            source_sequence=request.source_sequence,
            source="CONTRACT_FIXTURE" if fixture else "BROKER_OBSERVED",
            healthy=True,
            authorization="READ_ONLY",
            symbols=symbols,
            quotes=list(quotes.values()),
            orders=records(reconcile.get("order", []), "order"),
            positions=records(reconcile.get("position", []), "position"),
            history=records(history.get("deal", []), "deal"),
            history_complete=False,
            restrictions=[
                "EXTERNAL_EXECUTION_DISABLED",
                "BOUNDED_HISTORY_ONLY",
                "SYMBOL_TRADABILITY_NOT_CERTIFIED",
            ],
        )
