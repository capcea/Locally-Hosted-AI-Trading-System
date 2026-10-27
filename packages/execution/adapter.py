"""Simulator observations conform to the same read contract; commands stay in the engine."""

from packages.brokers.contracts import (
    BrokerSnapshot,
    BrokerSymbol,
    ObservedOrder,
    ReadOnlyAdapter,
    SnapshotRequest,
)
from packages.execution.contracts import SimState


class SimulatorAdapter(ReadOnlyAdapter):
    def __init__(self, state: SimState, account_id: str) -> None:
        self.state, self.account_id = state, account_id

    def snapshot(self, request: SnapshotRequest) -> BrokerSnapshot:
        if request.account_id != self.account_id or request.server != "SYNTHETIC_BROKER":
            raise PermissionError("Synthetic account identity mismatch")
        state = self.state
        spec = state.spec
        symbol = BrokerSymbol(
            broker_symbol=spec.symbol,
            symbol_id=spec.symbol,
            canonical_symbol=spec.canonical_symbol,
            digits=spec.digits,
            tick_size=spec.tick_size,
            contract_size=spec.contract_size,
            min_volume=spec.min_volume,
            max_volume=spec.max_volume,
            volume_step=spec.volume_step,
            observed_at=state.clock,
            source="SIMULATED",
            supported_order_types=list(spec.order_types),
            account_currency=state.model.account_currency,
        )
        orders = [
            ObservedOrder(
                broker_id=o.broker_order_id or str(o.id),
                symbol=spec.symbol,
                side=o.request.side,
                state=o.state,
                volume=o.request.volume - o.filled_volume,
                price=o.request.price,
                stop_loss=o.request.stop_loss,
                take_profit=o.request.take_profit,
                observed_at=state.clock,
                source_sequence=request.source_sequence,
            )
            for o in state.orders.values()
        ]
        positions = [
            ObservedOrder(
                broker_id=str(p.id),
                symbol=p.symbol,
                side=p.side,
                state="OPEN",
                volume=p.volume,
                price=p.entry_price,
                stop_loss=p.stop_loss,
                take_profit=p.take_profit,
                observed_at=state.clock,
                source_sequence=request.source_sequence,
            )
            for p in state.positions.values()
            if p.volume
        ]
        return BrokerSnapshot(
            provider="SIMULATOR",
            environment="SIMULATED",
            account_id=self.account_id,
            server="SYNTHETIC_BROKER",
            account_mode=spec.account_mode,
            currency=state.model.account_currency,
            balance=state.cash,
            equity=None,
            observed_at=state.clock,
            source_sequence=request.source_sequence,
            source="SIMULATED",
            healthy=state.connection == "CONNECTED",
            authorization="READ_ONLY",
            symbols=[symbol],
            quotes=[state.quote] if state.quote else [],
            orders=orders,
            positions=positions,
            restrictions=["SYNTHETIC_ASSUMPTIONS_ONLY", "EXTERNAL_EXECUTION_DISABLED"],
        )
