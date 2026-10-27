"""Fixed-code monitor entry point shared by independent worker and explicit owner checks."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.execution.contracts import SimState
from packages.execution.models import SimulationRun
from packages.persistence.models import TradingAccount, utcnow
from packages.risk.gateway import refresh
from packages.risk.ledger import incident, lock_account, verify_ledger
from packages.risk.models import AccountControl
from packages.risk.policy import applicable_policy, profiles


def poll(db: Session, account: TradingAccount) -> list[str]:
    account = lock_account(db, account.id)
    control = db.get(AccountControl, account.id)
    if control is None:
        return ["RISK_CONFIGURATION_REQUIRED"]
    if not verify_ledger(db, control):
        control.automatic_stop = True
        control.reasons = sorted(set(control.reasons) | {"RISK_LEDGER_INTEGRITY_FAILURE"})
        incident(db, account, "RISK_LEDGER_INTEGRITY_FAILURE")
        return ["RISK_LEDGER_INTEGRITY_FAILURE"]
    states = list(db.scalars(select(SimulationRun).where(SimulationRun.account_id == account.id)))
    if not states:
        # No synthetic clock exists yet; do not seed historical simulation time with wall time.
        try:
            applicable_policy(db, account, utcnow())
            profiles(db, account.id, {"ACCOUNT"})
        except ValueError as error:
            control.automatic_stop = True
            control.reasons = sorted(set(control.reasons) | {str(error)})
            return [str(error)]
        control.monitor_at = utcnow()
        return ["NO_SIMULATED_RUN"]
    at = max(SimState.model_validate(run.state).clock for run in states)
    if control.clock:
        at = max(at, control.clock)
    reasons = refresh(db, account, control, at)
    control.monitor_at = utcnow()
    return reasons
