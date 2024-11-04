import os
from minio import Minio
from minio.error import S3Error
from uuid import uuid4
from datetime import timedelta

from settings import settings
from minio_db.minio_manager import minio_client


def upload_image(file, user_id: int, filename: str) -> str:
    """
    Uploads an image to MinIO and returns the object name.

    :param file: The file object (UploadFile)
    :param user_id: ID of the user uploading the image
    :param filename: Original filename
    :return: Object name in MinIO
    """
    # Generate a unique object name to prevent collisions
    extension = os.path.splitext(filename)[1]
    object_name = f"user_{user_id}/{uuid4().hex}{extension}"

    # Calculate file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    try:
        minio_client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file.file,
            length=file_size,  # -1 means the length is unknown; minio can handle streaming
            content_type=file.content_type
        )
    except S3Error as e:
        print(f"Error uploading image: {e}")
        raise e

    return object_name


def get_image_url(object_name: str, expires: int = 3600) -> str:
    """
    Generates a pre-signed URL for the image.

    :param object_name: The object name in MinIO
    :param expires: Time in seconds for the URL to expire
    :return: Pre-signed URL as a string
    """
    try:
        expires_delta = timedelta(seconds=expires)
        url = minio_client.presigned_get_object(settings.MINIO_BUCKET_NAME, object_name, expires=expires_delta)
    except S3Error as e:
        print(f"Error generating pre-signed URL: {e}")
        raise e

    return url
