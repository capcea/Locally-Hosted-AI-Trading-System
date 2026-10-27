"""Closed round trips from actual journal fills, including fees and modeled funding."""

from decimal import Decimal, localcontext
from typing import Any

from sqlalchemy.orm import Session

from packages.execution.contracts import SimState
from packages.risk.models import Reservation, RiskAuthorization

D = Decimal


def round_trips(
    db: Session, state: SimState, regimes: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    cycles = []
    active: dict[str, dict[str, Any]] = {}
    with localcontext() as context:
        context.prec = 80
        for fill in state.fills:
            identity = str(fill.position_id)
            cycle = active.setdefault(
                identity,
                {
                    "fills": [],
                    "volume": D(0),
                    "weighted_seconds": D(0),
                    "last_at": fill.timestamp,
                    "risk": D(0),
                },
            )
            cycle["weighted_seconds"] += cycle["volume"] * D(
                str((fill.timestamp - cycle["last_at"]).total_seconds())
            )
            cycle["last_at"] = fill.timestamp
            cycle["fills"].append(fill)
            if fill.reason == "ORDER":
                cycle["volume"] += fill.volume
                if fill.order_id:
                    reservation = db.get(Reservation, fill.order_id)
                    auth = (
                        db.get(RiskAuthorization, reservation.authorization_id)
                        if reservation
                        else None
                    )
                    order = state.orders.get(str(fill.order_id))
                    if auth and order:
                        cycle["risk"] += (
                            D(str(auth.scope["estimated_risk"]))
                            * fill.volume
                            / order.request.volume
                        )
            else:
                cycle["volume"] -= fill.volume
            if cycle["volume"] < 0:
                raise ValueError("TRADE_INVENTORY_INCONSISTENT")
            if cycle["volume"] == 0:
                cycles.append(cycle)
                del active[identity]
        if any(c["volume"] for c in active.values()):
            raise ValueError("RESULT_CONTAINS_OPEN_INVENTORY")
        total_weight = sum((c["weighted_seconds"] for c in cycles), D(0))
        allocated = D(0)
        trades = []
        for index, cycle in enumerate(cycles):
            group = cycle["fills"]
            first, last = group[0], group[-1]
            funding = (
                (
                    state.swap - allocated
                    if index == len(cycles) - 1
                    else (state.swap * cycle["weighted_seconds"] / total_weight).quantize(
                        D(".000000000001")
                    )
                )
                if total_weight
                else D(0)
            )
            allocated += funding
            fees = sum((f.commission for f in group), D(0))
            net = sum((f.realized_pnl for f in group), D(0)) - fees + funding
            risk = cycle["risk"]
            trades.append(
                {
                    "instrument": state.spec.canonical_symbol,
                    "regime": (regimes or {}).get(str(first.order_id), "UNCLASSIFIED"),
                    "net": str(net),
                    "holding_seconds": (last.timestamp - first.timestamp).total_seconds(),
                    "realized_r": str(net / risk) if risk else None,
                    "initial_risk": str(risk),
                    "session_utc": first.timestamp.hour,
                    "fees": str(fees),
                    "funding": str(funding),
                    "entry_at": first.timestamp.isoformat(),
                    "exit_at": last.timestamp.isoformat(),
                    "funding_allocation": (
                        "actual run funding allocated by volume-time; final residual exact"
                    ),
                }
            )
        return trades
