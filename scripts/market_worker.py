"""Run only the fixed market data ingestion pipeline; never arbitrary code."""

import argparse
import os
import signal
import time
from pathlib import Path

from apps.api.config import Settings
from packages.market.jobs import Worker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    worker = Worker(
        Settings(_env_file=None if os.environ.get("APP_ENVIRONMENT") == "test" else ".env")
    )
    running = True

    def stop(signum: int, frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while running:
            worker.once()
            Path("/tmp/market-worker.ready").touch()  # noqa: S108 - owned container tmpfs, no secret data
            if args.once:
                break
            time.sleep(1)
    finally:
        worker.close()


if __name__ == "__main__":
    main()
