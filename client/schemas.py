from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

from client.models import SettingType
from camera.schemas import CameraInDB


class ClientBase(BaseModel):
    ip: str
    port: int
    auth_token: str

class ClientCreate(ClientBase):
    lpr_id: int
    camera_ids: List[int] = []



class LPRBase(BaseModel):
    name: str
    description: str
    value: str
    type: SettingType = Field(default=SettingType.STRING)

class LPRCreate(LPRBase):
    pass

class LPRUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    type: Optional[SettingType] = None

class LPRInDB(LPRBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    clients: List['ClientInDB'] = []

    class Config:
        from_attributes = True


class ClientInDB(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    lpr_id: int
    # lprs: List[LPRInDB] = []
    cameras: List[CameraInDB] = []
