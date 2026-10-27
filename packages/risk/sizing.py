"""Exact conservative sizing for explicitly verified linear payoff conventions."""

from datetime import datetime, timedelta
from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, Decimal, localcontext

from pydantic import ValidationError

from packages.execution.contracts import OrderRequest, Quote, SymbolSpec
from packages.risk.contracts import Decision, FinancialTerms, FXQuote

ZERO = Decimal(0)
MONEY = Decimal("0.00000001")


def ceil_money(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 80
        return value.quantize(MONEY, rounding=ROUND_CEILING)


def floor_money(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 80
        return value.quantize(MONEY, rounding=ROUND_FLOOR)


def loss_conversion(
    source: str, target: str, quotes: list[FXQuote], at: datetime, *, liability: bool = True
) -> Decimal:
    if source == target:
        return Decimal(1)
    paths: list[Decimal] = []

    def visit(currency: str, rate: Decimal, visited: frozenset[str]) -> None:
        if currency == target:
            paths.append(rate)
            return
        if len(visited) >= 4:
            return
        for quote in quotes:
            if (
                not quote.observed_at <= quote.available_at <= at <= quote.valid_until
                or at - quote.observed_at > timedelta(seconds=30)
            ):
                continue
            if currency == quote.base and quote.quote not in visited:
                visit(
                    quote.quote,
                    rate * (quote.ask if liability else quote.bid),
                    visited | {quote.quote},
                )
            elif currency == quote.quote and quote.base not in visited:
                visit(
                    quote.base,
                    rate / (quote.bid if liability else quote.ask),
                    visited | {quote.base},
                )

    with localcontext() as context:
        context.prec = 80
        visit(source, Decimal(1), frozenset({source}))
    if not paths:
        raise ValueError("FX_CONVERSION_MISSING_OR_STALE")
    # Differing explicit routes are contradictory; do not select an optimistic path.
    if len(set(paths)) != 1:
        raise ValueError("CONTRADICTORY_FX_PATHS")
    return paths[0]


def payoff_multiplier(spec: SymbolSpec, terms: FinancialTerms, at: datetime) -> Decimal:
    if not terms.verified_at <= at <= terms.valid_until:
        raise ValueError("FINANCIAL_TERMS_STALE_OR_UNVERIFIED")
    if terms.payoff not in {"LINEAR_CONTRACT", "LINEAR_TICK"}:
        raise ValueError("UNSUPPORTED_OR_UNVERIFIED_PAYOFF")
    if spec.asset_class == "FOREX" and not terms.base_currency:
        raise ValueError("FOREX_CURRENCIES_REQUIRED")
    if spec.asset_class not in {"FOREX", "METAL", "INDEX", "CRYPTO"}:
        raise ValueError("UNSUPPORTED_ASSET_CLASS")
    if terms.quote_currency != spec.profit_currency:
        raise ValueError("PROFIT_QUOTE_CURRENCY_MISMATCH")
    if (
        terms.payoff == "LINEAR_CONTRACT"
        and terms.tick_value_profit_currency != spec.tick_size * spec.contract_size
    ):
        raise ValueError("CONTRADICTORY_TICK_VALUE")
    return (
        spec.contract_size
        if terms.payoff == "LINEAR_CONTRACT"
        else terms.tick_value_profit_currency / spec.tick_size
    )


def size(
    spec: SymbolSpec,
    terms: FinancialTerms,
    quote: Quote,
    order: OrderRequest,
    at: datetime,
    account_currency: str,
    budget: Decimal,
    margin_available: Decimal,
    commission_per_unit: Decimal,
    slippage_ticks: int,
    *,
    auto_size: bool = False,
    execution_price: Decimal | None = None,
) -> Decision:
    try:
        with localcontext() as context:
            context.prec = 80
            budget = floor_money(budget)
            margin_available = floor_money(margin_available)
            if not spec.observed_at <= at <= spec.valid_until:
                raise ValueError("SYMBOL_SPEC_STALE")
            multiplier = payoff_multiplier(spec, terms, at)
            conversion = loss_conversion(spec.profit_currency, account_currency, terms.fx, at)
            if quote.symbol != spec.symbol or quote.available_at > at:
                raise ValueError("QUOTE_SYMBOL_OR_AVAILABILITY_MISMATCH")
            if order.stop_loss is None or order.take_profit is None:
                raise ValueError("SL_AND_TP_REQUIRED")
            if any(
                p is not None and p % spec.tick_size
                for p in (order.price, order.stop_loss, order.take_profit)
            ):
                raise ValueError("PROTECTION_OFF_TICK_GRID")
            entry = (
                execution_price or order.price or (quote.ask if order.side == "BUY" else quote.bid)
            )
            stop, take = order.stop_loss, order.take_profit
            if (
                (stop >= entry or take <= entry)
                if order.side == "BUY"
                else (stop <= entry or take >= entry)
            ):
                raise ValueError("INVALID_PROTECTION_GEOMETRY")
            if spec.stop_distance is None:
                raise ValueError("STOP_DISTANCE_UNVERIFIED")
            if min(abs(entry - stop), abs(entry - take)) < spec.stop_distance:
                raise ValueError("STOP_DISTANCE_TOO_SMALL")
            price_risk = abs(entry - stop) + spec.tick_size * Decimal(slippage_ticks) * (
                1 if execution_price is not None else 2
            )
            unit_risk = ceil_money(
                price_risk * multiplier * conversion
                + commission_per_unit * 2
                + terms.funding_buffer_per_unit
            )
            if unit_risk <= 0 or terms.margin_per_unit is None:
                raise ValueError("MARGIN_OR_MONETARY_RISK_UNVERIFIED")
            maximum = min(
                spec.max_volume,
                max(ZERO, budget) / unit_risk,
                max(ZERO, margin_available) / terms.margin_per_unit,
            )
            maximum = (maximum / spec.volume_step).to_integral_value(
                rounding=ROUND_DOWN
            ) * spec.volume_step
            volume = maximum if auto_size else order.volume
            if maximum < spec.min_volume:
                raise ValueError("MINIMUM_VOLUME_EXCEEDS_RISK_OR_MARGIN")
            if not spec.min_volume <= volume <= spec.max_volume or volume % spec.volume_step:
                raise ValueError("ILLEGAL_VOLUME_GRID")
            risk, margin = (
                ceil_money(volume * unit_risk),
                ceil_money(volume * terms.margin_per_unit),
            )
            if risk > budget or margin > margin_available:
                return Decision(
                    decision="DENY",
                    reasons=["RISK_OR_MARGIN_BUDGET_EXCEEDED"],
                    maximum_volume=maximum,
                    risk_per_unit=unit_risk,
                    estimated_risk=risk,
                    estimated_margin=margin,
                    available_budget=max(ZERO, budget),
                )
            return Decision(
                decision="ALLOW",
                reasons=["SIMULATED_SCOPE_ONLY"],
                approved_volume=volume,
                maximum_volume=maximum,
                estimated_risk=risk,
                risk_per_unit=unit_risk,
                estimated_margin=margin,
                available_budget=budget,
                evidence={"loss_conversion": str(conversion), "payoff_multiplier": str(multiplier)},
            )
    except (ValueError, ArithmeticError) as error:
        return Decision(
            decision="INDETERMINATE",
            reasons=[
                str(error)
                if isinstance(error, ValueError) and not isinstance(error, ValidationError)
                else "NUMERIC_OR_INPUT_RANGE_EXCEEDED"
            ],
        )
