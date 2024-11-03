import os
from minio import Minio
from minio.error import S3Error

from settings import settings


# MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
# MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "YOURACCESSKEY")
# MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "YOURSECRETKEY")
# MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "False") == "True"
# MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "user-profiles")

# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL
)

# Ensure the bucket exists
found = minio_client.bucket_exists(settings.MINIO_BUCKET_NAME)
if not found:
    minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
    print(f"Bucket '{settings.MINIO_BUCKET_NAME}' created.")
else:
    print(f"Bucket '{settings.MINIO_BUCKET_NAME}' already exists.")
