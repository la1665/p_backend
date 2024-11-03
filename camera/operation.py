from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError

from building_gate.operation import get_gate
from camera.models import Camera, CameraSetting
from camera.schemas import (CameraSettingCreate,CameraSettingUpdate, CameraSettingInDB,
    CameraCreate,CameraUpdate, CameraInDB)


async def get_setting(db: AsyncSession, setting_id: int):
    result = await db.execute(
        select(CameraSetting).where(CameraSetting.id==setting_id)
        .options(selectinload(CameraSetting.cameras))
    )
    setting =  result.unique().scalars().first()

    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")

    return setting

async def get_settings(db: AsyncSession, skip: int=0, limit: int=10):
    settings = await db.execute(select(CameraSetting)
        .offset(skip).limit(limit)
        .options(selectinload(CameraSetting.cameras))
    )
    return settings.unique().scalars().all()

async def create_setting(db: AsyncSession, setting: CameraSettingCreate):
    try:
        new_setting = CameraSetting(
        name=setting.name,
        description=setting.description,
        value=setting.value,
        setting_type=setting.setting_type
        )
        db.add(new_setting)
        await db.commit()
        await db.refresh(new_setting)
        result = await db.execute(
                select(CameraSetting)
                .where(CameraSetting.id == new_setting.id)
                .options(selectinload(CameraSetting.cameras))
            )
        new_setting = result.scalars().first()
        return new_setting
    except SQLAlchemyError as error:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create setting")

async def update_setting(db: AsyncSession, setting_id: int, setting: CameraSettingUpdate):
        db_setting = await get_setting(db, setting_id)
        update_data = setting.dict(exclude_unset=True)
        try:
            for key, value in update_data.items():
                setattr(db_setting, key, value)
            await db.commit()
            await db.refresh(db_setting)
            return db_setting
        except SQLAlchemyError as error:
            await db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not update setting")


async def delete_setting(db: AsyncSession, setting_id: int):
    db_setting = await get_setting(db, setting_id)
    try:
        await db.delete(db_setting)
        await db.commit()
        return db_setting
    except SQLAlchemyError as error:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not delete setting")


async def get_camera(db: AsyncSession, camera_id: int):
    result = await db.execute(select(Camera)
        .where(Camera.id==camera_id)
        .options(selectinload(Camera.settings))
    )
    camera =  result.unique().scalars().first()

    if camera is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Building not found")

    return camera

async def get_cameras(db: AsyncSession, skip: int=0, limit: int=10):
    cameras = await db.execute(
        select(Camera)
        .options(selectinload(Camera.settings))
        .offset(skip).limit(limit)
    )
    return cameras.unique().scalars().all()

async def create_camera(db: AsyncSession, camera: CameraCreate):

    db_gate = await get_gate(db, camera.gate_id)
    try:
        db_camera = Camera(
            name=camera.name,
            location=camera.location,
            latitude=camera.latitude,
            longitude=camera.longitude,
            gate_id=db_gate.id
        )
        if camera.settings:
            result = await db.execute(select(CameraSetting).where(CameraSetting.id.in_(camera.settings)))
            settings = result.scalars().all()
            if len(settings) != len(camera.settings):
                raise HTTPException(status_code=404, detail="One or more settings not found")
            db_camera.settings.extend(settings)
        db.add(db_camera)
        await db.commit()
        await db.refresh(db_camera)
        return db_camera

    except SQLAlchemyError as error:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create camera")


async def update_camera(db: AsyncSession, camera_id: int, camera: CameraUpdate):
    db_camera = await get_camera(db, camera_id)

    update_data = camera.dict(exclude_unset=True)
    if "gate_id" in update_data:
        gate_id = update_data["gate_id"]
        await get_gate(db, gate_id)

    for key, value in update_data.items():
        setattr(db_camera, key, value)
    try:
        await db.commit()
        await db.refresh(db_camera)
        return db_camera
    except SQLAlchemyError as error:
            await db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not update camera")

async def delete_camera(db: AsyncSession, camera_id: int):
    db_camera = await get_camera(db, camera_id)
    try:

        await db.delete(db_camera)
        await db.commit()
        return db_camera

    except SQLAlchemyError as error:
            await db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not delete camera")
