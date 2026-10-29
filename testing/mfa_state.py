"""Only age disposable browser sessions; never grant authentication or touch real installations."""

import argparse
import os
import re
import stat
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from scripts.integration_services import IsolatedServices


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["stale-mfa", "expire"])
    parser.add_argument("session", type=UUID)
    args = parser.parse_args()
    filename = os.environ.get("PHASE0_TEST_CONFIG")
    database = os.environ.get("E2E_AUTH_DATABASE", "")
    if (
        os.environ.get("E2E_PHASE1_ISOLATED") != "1"
        or not filename
        or not re.fullmatch(r"p1_browser_[a-f0-9]{32}", database)
    ):
        raise RuntimeError("Disposable browser harness required; ambient sessions are prohibited")
    path = Path(filename)
    info = path.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
        or info.st_uid != os.getuid()
    ):
        raise RuntimeError("Private disposable harness configuration required")
    isolated = IsolatedServices.model_validate_json(path.read_bytes())
    url = make_url(isolated.database_url).set(drivername="postgresql", database=database)
    field = "mfa_at" if args.action == "stale-mfa" else "idle_expires_at"
    with psycopg.connect(url.render_as_string(hide_password=False)) as db:
        result = db.execute(
            sql.SQL(
                "UPDATE login_sessions SET {} = CURRENT_TIMESTAMP - INTERVAL '6 minutes' "
                "WHERE id = %s"
            ).format(sql.Identifier(field)),
            (args.session,),
        )
        if result.rowcount != 1:
            raise RuntimeError("Disposable session not found")
    print("Disposable authorization aged; no credentials, MFA enrollment or grants changed.")


if __name__ == "__main__":
    main()
