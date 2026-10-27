"""Independent fixed-code simulated-risk monitor; no broker or generated-code capability."""

import argparse
import os
import signal
import time
from pathlib import Path

from sqlalchemy import select, text

from apps.api.config import Settings
from packages.persistence.audit import append_event
from packages.persistence.models import TradingAccount
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = Settings(_env_file=None if os.environ.get("APP_ENVIRONMENT") == "test" else ".env")
    if not settings.database_url or not settings.auth_encryption_key:
        raise RuntimeError("Restricted database identity and private risk key required")
    store = Store(settings.database_url.get_secret_value())
    running = True

    def stop(signum: int, frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        with store.session() as db:
            role = db.execute(
                text(
                    "SELECT rolsuper,rolcreaterole,rolcreatedb FROM pg_roles "
                    "WHERE rolname=current_user"
                )
            ).one()
            if any(role) or db.scalar(
                text("SELECT has_table_privilege(current_user,'risk_ledger','UPDATE')")
            ):
                raise RuntimeError("Risk monitor refuses privileged database identities")
        while running:
            count = once(store, settings.auth_encryption_key.get_secret_value())
            Path("/tmp/risk-monitor.ready").touch()  # noqa: S108 - private container tmpfs heartbeat
            if args.once:
                print(f"PASSED: fixed risk monitor checked {count} configured SIMULATED accounts.")
                break
            time.sleep(5)
    finally:
        store.engine.dispose()


if __name__ == "__main__":
    main()
