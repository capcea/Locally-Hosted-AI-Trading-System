"""Bound expensive data reads independently of the ingestion worker slots."""

from collections.abc import Iterator
from threading import BoundedSemaphore
from typing import Annotated

from fastapi import Depends, HTTPException

SLOTS = BoundedSemaphore(2)


def query_slot() -> Iterator[None]:
    if not SLOTS.acquire(blocking=False):
        raise HTTPException(429, "Concurrent market-query limit reached")
    try:
        yield
    finally:
        SLOTS.release()


QuerySlot = Annotated[None, Depends(query_slot)]
