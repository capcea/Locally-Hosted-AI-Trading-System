"""Independent fixed-code simulated-risk monitor; no broker or generated-code capability."""

import argparse
import os
import signal
from pathlib import Path
from threading import Event

from sqlalchemy import select, text
from sqlalchemy.exc import DisconnectionError, OperationalError

from apps.api.config import Settings
from packages.persistence.audit import append_event
from packages.persistence.models import TradingAccount, User
from packages.persistence.store import Store
from packages.research.models import ResearchAccount
from packages.risk.models import AccountControl
from packages.risk.monitor import poll


def once(store: Store, key: str) -> int:
    with store.session() as db:
        accounts = list(
            db.scalars(
                select(AccountControl.account_id)
                .where(AccountControl.account_id.not_in(select(ResearchAccount.account_id)))
                .order_by(AccountControl.account_id)
                .limit(1000)
            )
        )
    checked = 0
    for account_id in accounts:
        with store.session() as db, db.begin():
            owner_id = db.scalar(
                select(TradingAccount.owner_id).where(TradingAccount.id == account_id)
            )
            if owner_id is None:
                continue
            # Authenticated requests serialize owner -> account -> audit head. Incident/ledger
            # inserts also take an owner FK lock, so taking the account first can deadlock them.
            # Read mutable account/control state only after the owner lock has been acquired.
            db.execute(select(User.id).where(User.id == owner_id).with_for_update()).scalar_one()
            account = db.get(TradingAccount, account_id)
            control = db.get(AccountControl, account_id)
            if account is None or control is None:
                continue
            before = (control.sequence, control.automatic_stop, tuple(control.reasons))
            reasons = poll(db, account)
            if (control.sequence, control.automatic_stop, tuple(control.reasons)) != before:
                append_event(
                    db,
                    key,
                    "risk.independent_monitor",
                    entity_id=account_id,
                    after={
                        "source": "SIMULATED",
                        "reasons": reasons,
                        "ledger_head": control.digest,
                    },
                )
            checked += 1
    return checked


def restricted_identity(store: Store) -> None:
    with store.session() as db:
        role = db.execute(
            text(
                "SELECT rolsuper,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=current_user"
            )
        ).one()
        if any(role) or db.scalar(
            text("SELECT has_table_privilege(current_user,'risk_ledger','UPDATE')")
        ):
            raise RuntimeError("Risk monitor refuses privileged database identities")


def monitor(
    store: Store,
    key: str,
    stopped: Event,
    *,
    single: bool = False,
    ready: Path = Path("/tmp/risk-monitor.ready"),  # noqa: S108 -- owned container tmpfs
) -> None:
    """Reconnect a bounded number of times; never publish health for a failed scan."""
    failures = 0
    if not single:
        ready.unlink(missing_ok=True)
    try:
        while not stopped.is_set():
            try:
                # Recheck on every connection/recovery, not just the initial process startup.
                restricted_identity(store)
                count = once(store, key)
            except (OperationalError, DisconnectionError) as error:
                if not single:
                    ready.unlink(missing_ok=True)
                failures += 1
                state = getattr(getattr(error, "orig", None), "sqlstate", None)
                transient = state is None or (
                    isinstance(state, str)
                    and (state.startswith("08") or state in {"57P01", "57P02", "57P03", "53300"})
                )
                if single or not transient or failures >= 6:
                    raise RuntimeError("RISK_MONITOR_DATABASE_UNAVAILABLE") from None
                store.engine.dispose()
                delay = min(2 ** (failures - 1), 8)
                print(
                    f"Risk monitor database unavailable; retry {failures}/6 in {delay}s. "
                    "Readiness withheld; fresh monitoring remains required.",
                    flush=True,
                )
                stopped.wait(delay)
                continue
            failures = 0
            if single:
                print(f"PASSED: fixed risk monitor checked {count} configured SIMULATED accounts.")
                break
            ready.touch()
            stopped.wait(5)
    finally:
        if not single:
            ready.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = Settings(_env_file=None if os.environ.get("APP_ENVIRONMENT") == "test" else ".env")
    if not settings.database_url or not settings.auth_encryption_key:
        raise RuntimeError("Restricted database identity and private risk key required")
    store = Store(settings.database_url.get_secret_value())
    stopped = Event()

    def stop(signum: int, frame: object) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        monitor(store, settings.auth_encryption_key.get_secret_value(), stopped, single=args.once)
    finally:
        store.engine.dispose()


if __name__ == "__main__":
    main()
