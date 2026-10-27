"""Frozen owner-reviewed scope and fixed trusted software identity, rechecked during work."""

import hashlib
import importlib.metadata
import platform
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.persistence.models import TradingAccount
from packages.research.contracts import ExperimentInput
from packages.research.models import ResearchRun
from packages.risk.models import AccountControl, ProfileBinding
from packages.risk.policy import applicable_policy, profiles

FILES = (
    "contracts.py",
    "strategies.py",
    "data.py",
    "screening.py",
    "statistics.py",
    "engine.py",
    "jobs.py",
    "walk_forward.py",
    "accounting.py",
    "approval.py",
    "access.py",
)


def software_manifest() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    targets = sorted(
        str(path.relative_to(root))
        for folder in ("packages", "apps/api/research")
        for path in (root / folder).rglob("*.py")
    ) + ["pyproject.toml", "uv.lock", "scripts/research_worker.py"]
    return {
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name) for name in ("pyarrow", "pydantic", "sqlalchemy")
        },
        "files": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in targets},
    }


def assert_current(db: Session, research: ResearchRun, plan: ExperimentInput) -> None:
    snapshot = research.approval_snapshot
    source = db.get(TradingAccount, plan.source_account_id)
    control = db.get(AccountControl, plan.source_account_id)
    if (
        source is None
        or source.archived
        or source.revision != snapshot["account_revision"]
        or control is None
        or control.manual_stop
        or control.automatic_stop
    ):
        raise ValueError("SOURCE_RISK_APPROVAL_REVOKED")
    if str(applicable_policy(db, source, plan.chronology.start).id) != snapshot["policy_id"]:
        raise ValueError("SOURCE_POLICY_VERSION_CHANGED")
    scopes = set(
        db.scalars(select(ProfileBinding.scope_key).where(ProfileBinding.account_id == source.id))
    )
    current = profiles(db, source.id, scopes | {"ACCOUNT"})
    if sorted(str(p.id) for p in current) != sorted(snapshot["profiles"]):
        raise ValueError("SOURCE_RISK_PROFILES_CHANGED")
    if software_manifest() != snapshot["software"]:
        raise ValueError("RESEARCH_SOFTWARE_VERSION_CHANGED")
