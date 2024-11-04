import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
from io import BytesIO
from minio.error import S3Error
from pydantic import EmailStr

from db.engine import get_db
from user.operations import UserOperation
from user.schemas import UserInDB, UserCreate, UserUpdate
from user.user_image import upload_image, get_image_url
from user.image_validater import validate_image_size, validate_image_extension, validate_image_content_type
from authentication.access_level import (get_user,
    get_current_active_user,
    get_admin_user,
    get_admin_or_staff_user,
)
from minio_db.minio_manager import minio_client
from settings import settings
from user.models import UserType

class TagType(Enum):
    ADMIN = "admin"
    STAFF = "staff"
    USER = "user"
    VIEWER = "viewer"


user_router = APIRouter()


@user_router.post("/v1/users", status_code=status.HTTP_201_CREATED)
async def api_create_user(username: str = Form(...),
    email: EmailStr = Form(...),
    user_type: UserType = Form(...),
    password: str = Form(...),
    profile_image: Optional[UploadFile]=File(None),
    db: AsyncSession=Depends(get_db),
    current_user: UserInDB=Depends(get_admin_user)):
    user = UserCreate(
            username=username,
            email=email,
            user_type=user_type.value,
            password=password,
        )
    # db_user = await UserOperation(db).check_for_user(user.username, user.email)
    # if db_user:
    #     raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, "Username/Email already exists.")
    if profile_image:
        await validate_image_extension(profile_image.filename)
        await validate_image_content_type(profile_image.content_type)
        await validate_image_size(profile_image)
    # print(user_type)
    # print(user_type.value)
    new_user =  await UserOperation(db).create_user(user)
    if profile_image:
        try:
            object_name = upload_image(profile_image, new_user.id, profile_image.filename)
            # Optionally, generate a pre-signed URL
            image_url = get_image_url(object_name)
            # Update the user's profile_image field
            # new_user.profile_image = object_name
            await UserOperation(db).update_user(new_user.id, {"profile_image": object_name})
            # You can return the URL or the object name based on your preference
            # Here, we return the object name and URL
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    **UserInDB.from_orm(new_user).dict(),
                    "profile_image_url": image_url
                }
            )
        except Exception as e:
            print(f"Error uploading profile image: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload profile image: {str(e)}"
            )
    return UserInDB.from_orm(new_user)



@user_router.get("/v1/users", response_model=List[UserInDB])
async def api_read_all_users(db: AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_user)):
    return await UserOperation(db).get_all_users()

@user_router.get("/v1/users/{user_id}")
async def api_read_user(user_id: int, db: AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_user)):
    user = await UserOperation(db).get_user(user_id)
    # if user is None:
    #     raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found!")
    if user.profile_image:
        try:
            image_url = get_image_url(user.profile_image)
            return {
                **UserInDB.from_orm(user).dict(),
                "profile_image_url": image_url
            }
        except Exception as e:
            # Log the error and proceed without the image URL
            print(f"Error generating image URL: {e}")
    return user

@user_router.delete("/v1/users/{user_id}")
async def api_delete_user(user_id: int, db:AsyncSession=Depends(get_db), current_user: UserInDB=Depends(get_admin_user)):
    user = await UserOperation(db).delete_user(user_id)
    # if user is None:
    #     raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return user


@user_router.patch("/v1/users/{user_id}")
async def api_change_user_activation(user_id: int, db:AsyncSession=Depends(get_db), current_user:UserInDB=Depends(get_admin_or_staff_user)):
    user = await UserOperation(db).update_user_activate_status(user_id)
    return {"msg": f"User with id:{user.id} is_active status updated to {user.is_active} successfully"}



@user_router.get("/users/{user_id}/profile-image", response_class=StreamingResponse)
async def get_profile_image(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Fetch and serve the user's profile image from MinIO.
    Accessible by all authenticated and active users.
    """
    user = await UserOperation(db).get_user(user_id)
    if not user or not user.profile_image:
        raise HTTPException(status_code=404, detail="Profile image not found.")

    try:
        response = minio_client.get_object(settings.MINIO_BUCKET_NAME, user.profile_image)
        return StreamingResponse(response, media_type="image/jpeg")  # Adjust media_type as needed
    except S3Error as e:
        print(f"Error fetching image: {e}")
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Failed to fetch profile image.")
