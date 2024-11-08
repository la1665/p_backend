from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Any, List, Optional, Sequence

from authentication.access_level import get_user
from user.models import DBUser, UserType
from user.schemas import UserBase, UserCreate, UserUpdate, UserInDB
from authentication.auth import get_password_hash


class UserOperation:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def check_for_user(self, username: Optional[str]=None, email: Optional[str]=None) -> bool:
        async with self.db_session as session:
            query = await session.execute(
                select(DBUser).where(
                    or_(DBUser.username == username, DBUser.email == email)
                ))
            db_user = query.unique().scalars().first()
            if db_user:
                return True
            else:
                return False

    async def create_user(self, user: UserCreate) -> DBUser:
        hashed_password = get_password_hash(user.password)
        async with self.db_session as session:

            query = await session.execute(
                select(DBUser).where(
                    or_(DBUser.username == user.username, DBUser.email == user.email)
                ))
            db_user = query.unique().scalars().first()
            if db_user:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "username/email already exists.")

            try:
                new_user = DBUser(
                    username=user.username,
                    email=user.email,
                    user_type=user.user_type,
                    hashed_password=hashed_password
                )
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                return new_user
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, f"{error}: Could not create user")

    async def get_all_users(self) -> Sequence[DBUser]:
        async with self.db_session as session:
            result = await session.execute(
                select(DBUser)
            )
            users = result.unique().scalars().all()
            return users

    async def get_user(self, user_id: int):
        async with self.db_session as session:
            result = await session.execute(
                select(DBUser).where(DBUser.id==user_id)
            )
            user = result.unique().scalars().first()
            if user is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found!")
            return user

    async def update_user(self, user_id: int, user_update: dict):
        async with self.db_session as session:
            user = await self.get_user(user_id)
            try:

                for key, value in user_update.items():
                    setattr(user, key, value)

                session.add(user)
                await session.commit()
                await session.refresh(user)
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to update user."
                )
            return user


    async def delete_user(self, user_id: int):
        async with self.db_session as session:
            user = await self.get_user(user_id)
            try:
                await session.delete(user)
                await session.commit()
                return user
            except SQLAlchemyError as error:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{error}: Could not delete user")

    async def update_user_activate_status(self, user_id:int):
        async with self.db_session as session:
            user = await self.get_user(user_id)
            if user.user_type not in [UserType.USER, UserType.VIEWER]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only change the is_active status of users with the 'user, viewer' role"
                    )

            user.is_active = not user.is_active

            try:
                await session.commit()
                await session.refresh(user)
                return user
            except:
                await session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Could not update user status")
