"""Official terminal reads only, on an explicitly pinned demo/investor Windows terminal."""

import importlib
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from packages.brokers.contracts import (
    BrokerSnapshot,
    BrokerSymbol,
    ObservedOrder,
    ReadOnlyAdapter,
    SnapshotRequest,
)
from packages.execution.contracts import Quote


def amount(value: object) -> Decimal:
    # The SDK exposes doubles. Preserve its decimal spelling, never claim greater source precision.
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("NONFINITE_TERMINAL_VALUE")
    return result


class MT5Adapter(ReadOnlyAdapter):
    def __init__(self, authorized_demo: bool, sdk: Any = None) -> None:
        if not authorized_demo:
            raise PermissionError("Explicit authorization for demo reads required")
        if sdk is None:
            if sys.platform != "win32":
                raise RuntimeError("Actual MT5 terminal integration requires Windows")
            sdk = importlib.import_module("MetaTrader5")
        self.sdk = sdk
        self.fixture = sys.platform != "win32" or getattr(sdk, "contract_fixture", False)

    def identity(self, request: SnapshotRequest) -> Any:
        terminal, account = self.sdk.terminal_info(), self.sdk.account_info()
        if (
            terminal is None
            or account is None
            or not terminal.connected
            or not terminal.tradeapi_disabled
            or account.trade_allowed
            or account.trade_mode != 0
            or str(account.login) != request.account_id
            or account.server != request.server
        ):
            raise PermissionError("PINNED_DEMO_INVESTOR_TERMINAL_REQUIRED")
        return account

    def snapshot(self, request: SnapshotRequest) -> BrokerSnapshot:
        if not self.sdk.initialize(timeout=10000):
            raise ConnectionError("MT5_TERMINAL_UNAVAILABLE")
        try:
            account = self.identity(request)
            symbols: list[BrokerSymbol] = []
            quotes: list[Quote] = []
            observed = datetime.now(UTC)
            for name in request.symbols:
                info = self.sdk.symbol_info(name)
                tick = self.sdk.symbol_info_tick(name)
                if info is None or tick is None or info.name != name:
                    raise ValueError("MT5_SYMBOL_UNAVAILABLE")
                symbols.append(
                    BrokerSymbol(
                        broker_symbol=name,
                        symbol_id=name,
                        digits=info.digits,
                        tick_size=amount(info.trade_tick_size)
                        if info.trade_tick_size > 0
                        else None,
                        contract_size=amount(info.trade_contract_size)
                        if info.trade_contract_size > 0
                        else None,
                        min_volume=amount(info.volume_min) if info.volume_min > 0 else None,
                        max_volume=amount(info.volume_max) if info.volume_max > 0 else None,
                        volume_step=amount(info.volume_step) if info.volume_step > 0 else None,
                        stop_distance=amount(info.trade_stops_level) * amount(info.point),
                        freeze_distance=amount(info.trade_freeze_level) * amount(info.point),
                        account_currency=account.currency,
                        observed_at=observed,
                        source="MT5_TERMINAL",
                        supported_order_types=[
                            name
                            for bit, name in ((1, "MARKET"), (2, "LIMIT"), (4, "STOP"))
                            if info.order_mode & bit
                        ],
                        metadata={
                            "trade_mode": int(info.trade_mode),
                            "order_mode_bits": int(info.order_mode),
                            "profit_currency": str(info.currency_profit),
                            "sessions_available": False,
                        },
                    )
                )
                event = datetime.fromtimestamp(tick.time_msc // 1000, UTC) + timedelta(
                    milliseconds=tick.time_msc % 1000
                )
                captured = datetime.now(UTC)
                quotes.append(
                    Quote(
                        symbol=name,
                        event_time=event,
                        available_at=captured,
                        sequence=request.source_sequence,
                        bid=amount(tick.bid),
                        ask=amount(tick.ask),
                    )
                )
            orders = self.sdk.orders_get()
            positions = self.sdk.positions_get()
            history = self.sdk.history_deals_get(
                observed - timedelta(days=request.history_days), observed
            )
            if any(rows is None or len(rows) > 500 for rows in (orders, positions, history)):
                raise ConnectionError("MT5_BOUNDED_RECONCILIATION_UNAVAILABLE")

            def records(rows: Any, category: str) -> list[ObservedOrder]:
                return [
                    ObservedOrder(
                        broker_id=str(row.ticket),
                        symbol=str(row.symbol),
                        side="BUY" if row.type in {0, 2, 4, 6} else "SELL",
                        state=category,
                        volume=amount(row.volume_current if category == "PENDING" else row.volume),
                        price=amount(row.price_open if category != "DEAL" else row.price),
                        stop_loss=amount(row.sl) if category != "DEAL" and row.sl > 0 else None,
                        take_profit=amount(row.tp) if category != "DEAL" and row.tp > 0 else None,
                        observed_at=datetime.now(UTC),
                        source_sequence=request.source_sequence,
                    )
                    for row in rows
                    if category != "DEAL" or row.type in {0, 1}
                ]

            # Detect a terminal account switch during the bounded read sequence.
            self.identity(request)
            return BrokerSnapshot(
                provider="MT5",
                environment="DEMO_READ_ONLY",
                account_id=str(account.login),
                server=account.server,
                currency=account.currency,
                account_mode="HEDGING"
                if account.margin_mode == 2
                else "NETTING"
                if account.margin_mode == 0
                else None,
                balance=amount(account.balance),
                equity=amount(account.equity),
                observed_at=datetime.now(UTC),
                source_sequence=request.source_sequence,
                source="CONTRACT_FIXTURE" if self.fixture else "BROKER_OBSERVED",
                healthy=True,
                authorization="READ_ONLY",
                symbols=symbols,
                quotes=quotes,
                orders=records(orders, "PENDING"),
                positions=records(positions, "OPEN"),
                history=records(history, "DEAL"),
                history_complete=False,
                restrictions=[
                    "EXTERNAL_EXECUTION_DISABLED",
                    "SDK_DOUBLE_SOURCE_PRECISION",
                    "BOUNDED_HISTORY_ONLY",
                ],
            )
        finally:
            self.sdk.shutdown()
