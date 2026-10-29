"""Near-worker campaign deadline/cancellation checks; no financial calculation changes."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.campaigns.models import CampaignExperiment, CampaignRuntime
from packages.persistence.models import utcnow
from packages.research.models import ResearchRun


def assert_campaign_authority(db: Session, run: ResearchRun) -> None:
    if run.id is None:
        return  # Source-snapshot preflight, not an actual submitted run.
    link = db.scalar(select(CampaignExperiment).where(CampaignExperiment.run_id == run.id))
    if link is None:
        return  # Ordinary Phase5 runs retain their existing authority.
    runtime = db.get(CampaignRuntime, link.campaign_id, populate_existing=True)
    if (
        runtime is None
        or runtime.owner_id != run.owner_id
        or not runtime.active
        or runtime.cancel_requested
        or runtime.deadline is None
        or runtime.deadline <= utcnow()
    ):
        raise ValueError("CAMPAIGN_AUTHORITY_EXPIRED_OR_STOPPED")
