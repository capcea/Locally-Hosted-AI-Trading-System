"""Pinned MinIO object versions with compliance retention and verified SHA-256."""

import hashlib
import io
from collections import OrderedDict
from datetime import timedelta
from threading import Lock
from urllib.parse import urlsplit

import urllib3
from minio import Minio
from minio.retention import Retention

from apps.api.config import Settings
from packages.persistence.models import utcnow


class DataIntegrityError(ValueError):
    pass


class ObjectStore:
    def __init__(self, config: Settings):
        if not (
            config.object_store_url
            and config.market_storage_user
            and config.market_storage_password
        ):
            raise RuntimeError("Market object storage is not configured")
        parsed = urlsplit(config.object_store_url)
        self.bucket = config.market_bucket
        self.retention_days = config.market_retention_days
        self._cache: OrderedDict[tuple[str, str, str, int], bytes] = OrderedDict()
        self._lock = Lock()
        self.client = Minio(
            parsed.netloc,
            access_key=config.market_storage_user.get_secret_value(),
            secret_key=config.market_storage_password.get_secret_value(),
            secure=parsed.scheme == "https",
            http_client=urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=3, read=20), retries=False
            ),
        )

    def put(self, key: str, content: bytes) -> dict[str, object]:
        result = self.client.put_object(
            self.bucket,
            key,
            io.BytesIO(content),
            len(content),
            retention=Retention("COMPLIANCE", utcnow() + timedelta(days=self.retention_days)),
        )
        if not result.version_id:
            raise DataIntegrityError("Storage must return an immutable object version")
        return {
            "key": key,
            "version": result.version_id,
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }

    def _read(self, key: str, version: str, digest: str, size: int) -> bytes:
        if size > 32 * 1024 * 1024 or size < 0:
            raise DataIntegrityError("Object exceeds bounded read size")
        identity = (key, version, digest, size)
        with self._lock:
            if identity in self._cache:
                self._cache.move_to_end(identity)
                return self._cache[identity]
        response = self.client.get_object(self.bucket, key, version_id=version)
        try:
            content = response.read(size + 1)
        finally:
            response.close()
            response.release_conn()
        if len(content) != size or hashlib.sha256(content).hexdigest() != digest:
            raise DataIntegrityError("Immutable object checksum verification failed")
        with self._lock:
            self._cache[identity] = content
            while len(self._cache) > 8:
                self._cache.popitem(last=False)
        return content

    def get(self, artifact: dict[str, object]) -> bytes:
        return self._read(
            str(artifact["key"]),
            str(artifact["version"]),
            str(artifact["sha256"]),
            int(str(artifact["bytes"])),
        )
