from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from building_gate.operation import get_gate
from camera.models import Camera
from client.models import LPR, Client


async def create_client(db: AsyncSession, client):
    # Ensure the LPR exists
    db_lpr = await get_lpr(db, client.lpr_id)

    try:
        # Create the new Client instance
        new_client = Client(
            ip=client.ip,
            port=client.port,
            auth_token=client.auth_token,
            lpr_id=db_lpr.id
        )

        # Assign cameras to the client
        if client.camera_ids:
            # Fetch the camera objects
            camera_result = await db.execute(select(Camera).where(Camera.id.in_(client.camera_ids)))
            cameras = camera_result.unique().scalars().all()

            # Ensure all requested cameras are found
            if len(cameras) != len(client.camera_ids):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more cameras not found")
            new_client.cameras.extend(cameras)
            # new_client.cameras = cameras

        # Add the client to the database
        db.add(new_client)
        await db.commit()
        await db.refresh(new_client)

        # result = await db.execute(
        #     select(Client)
        #     .where(Client.id == new_client.id)
        #     .options(selectinload(Client.cameras), selectinload(Client.lpr))
        # )

        # Retrieve the client object with all related data properly loaded
        # client_with_cameras = result.unique().scalars().first()

        # return client_with_cameras
        return new_client
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def get_lpr(db: AsyncSession, lpr_id: int):
    result = await db.execute(select(LPR).where(LPR.id == lpr_id).options(selectinload(LPR.clients)))
    lpr =  result.unique().scalars().first()

    if lpr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="lpr not found")
    return lpr

async def get_lprs(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(LPR).options(selectinload(LPR.clients)).offset(skip).limit(limit))
    return result.unique().scalars().all()

async def create_lpr(db: AsyncSession, lpr):
    new_lpr = LPR(name=lpr.name,
        description=lpr.description,
        value=lpr.value,
        type=lpr.type
)
    try:
        db.add(new_lpr)
        await db.commit()
        await db.refresh(new_lpr)
        result = await db.execute(
            select(LPR)
            .where(LPR.id == new_lpr.id)
            .options(selectinload(LPR.clients))  # Use selectinload to eager-load the relationship
        )
        lpr_with_clients = result.scalars().first()

        return lpr_with_clients
        # return new_lpr
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

async def update_lpr(db: AsyncSession, lpr_id: int, lpr):
    db_lpr = await get_lpr(db, lpr_id)
    update_data = lpr.dict(exclude_unset=True)

    for key, value in lpr.dict(exclude_unset=True).items():
        setattr(db_lpr, key, value)
    try:
        await db.commit()
        await db.refresh(db_lpr)
        return db_lpr
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

async def delete_lpr(db: AsyncSession, lpr_id: int):
    db_lpr = await get_lpr(db, lpr_id)
    try:
        await db.delete(db_lpr)
        await db.commit()
        return db_lpr
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
