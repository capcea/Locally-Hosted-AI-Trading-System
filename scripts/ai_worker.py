"""Trusted inference transport only; no generation/execution agents or trading credentials."""

import argparse
import signal
import time
from pathlib import Path

from packages.ai.settings import GatewaySettings
from packages.ai.worker import Worker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    worker = Worker(GatewaySettings())
    running = True

    def stop(signum: int, frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        while running:
            try:
                worked = worker.once()
                Path("/tmp/ai-worker.ready").touch()  # noqa: S108 - owned, non-secret container tmpfs
            except Exception:
                print('{"event":"AI_WORKER_STORAGE_UNAVAILABLE"}', flush=True)
                worked = False
            if args.once:
                break
            if not worked:
                time.sleep(1)
    finally:
        worker.close()


if __name__ == "__main__":
    main()
