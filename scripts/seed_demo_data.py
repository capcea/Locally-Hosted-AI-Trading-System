"""Seed an explicit configuration fixture, not prices, fills or performance."""

import json
from pathlib import Path

from packages.domain.contracts import ReferenceProfile


def seed(destination: Path = Path("data/fixtures/reference-account.json")) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "environment": "SIMULATED",
                "source": "SYNTHETIC_TEST_FIXTURE",
                "market_data": False,
                "performance_data": False,
                "account": ReferenceProfile().model_dump(mode="json"),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    seed()
    print("Seeded data/fixtures/reference-account.json (SYNTHETIC_TEST_FIXTURE; no market data).")
