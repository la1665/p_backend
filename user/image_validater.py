from fastapi import UploadFile, HTTPException, status
from typing import List
import imghdr

# Define allowed image MIME types and extensions
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]
ALLOWED_EXTENSIONS = ["jpeg", "jpg", "png"]

# Define maximum file size (in bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


async def validate_image_extension(filename: str):
    """
    Validates the file extension of the uploaded image.

    :param filename: Name of the uploaded file
    :raises HTTPException: If the file extension is not allowed
    """
    extension = filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '.{extension}'. Allowed extensions: {ALLOWED_EXTENSIONS}",
        )


async def validate_image_content_type(content_type: str):
    """
    Validates the MIME type of the uploaded image.

    :param content_type: MIME type of the uploaded file
    :raises HTTPException: If the MIME type is not allowed
    """
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type '{content_type}'. Allowed types: {ALLOWED_MIME_TYPES}",
        )


async def validate_image_size(file: UploadFile):
    """
    Validates the size of the uploaded image.

    :param file: UploadFile object
    :raises HTTPException: If the file size exceeds the maximum limit
    """
    file.file.seek(0, 2)  # Move the cursor to the end of the file
    file_size = file.file.tell()
    file.file.seek(0)  # Reset the cursor to the beginning of the file
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )


# async def validate_image_content(file: UploadFile):
#     """
#     Validates the actual content of the uploaded image to prevent spoofing.

#     :param file: UploadFile object
#     :raises HTTPException: If the file content does not match its extension or MIME type
#     """
#     # Read a small portion of the file to determine its type
#     content = await file.read(512)
#     file.file.seek(0)  # Reset the cursor after reading
#     file_type = imghdr.what(None, h=content)

#     if file_type not in ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Uploaded file content does not match its extension.",
#         )
