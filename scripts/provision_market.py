"""Migration-time provisioning; storage administrator credentials never reach the API worker."""

from urllib.parse import urlsplit

from minio import Minio
from minio.credentials.providers import StaticProvider
from minio.error import MinioAdminException
from minio.minioadmin import MinioAdmin


def provision_storage(
    endpoint: str, root_user: str, root_password: str, user: str, password: str, bucket: str
) -> None:
    url = urlsplit(endpoint)
    client = Minio(
        url.netloc, access_key=root_user, secret_key=root_password, secure=url.scheme == "https"
    )
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket, object_lock=True)
    lock = client.get_object_lock_config(bucket)
    if not lock:
        raise RuntimeError("Market bucket must have object locking enabled")
    admin = MinioAdmin(
        endpoint=url.netloc,
        credentials=StaticProvider(root_user, root_password),
        secure=url.scheme == "https",
    )
    try:
        admin.user_info(user)
    except MinioAdminException as error:
        if "XMinioAdminNoSuchUser" not in str(error):
            raise
        admin.user_add(user, password)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetBucketLocation"],
                "Resource": [f"arn:aws:s3:::{bucket}"],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:PutObject",
                    "s3:PutObjectRetention",
                ],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            },
        ],
    }
    name = f"market-{bucket}"
    admin.policy_add(name, policy=policy)
    admin.policy_set(name, user=user)
