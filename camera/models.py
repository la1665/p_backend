from enum import Enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime,Table, UUID, func
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as sqlEnum

from db.engine import Base
from client.models import client_camera_association

class SettingType(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"

camera_settings_association = Table(
    'camera_settings_association', Base.metadata,
    Column('camera_id', Integer, ForeignKey('cameras.id'), primary_key=True),
    Column('setting_id', Integer, ForeignKey('camera_settings.id'), primary_key=True)
)

class CameraSetting(Base):
    __tablename__ = 'camera_settings'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    value = Column(String(255), nullable=False)
    setting_type = Column(sqlEnum(SettingType),default=SettingType.STRING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    cameras = relationship("Camera", secondary=camera_settings_association, back_populates="settings")

class Camera(Base):
    __tablename__ = 'cameras'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=True)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    gate_id = Column(Integer, ForeignKey('gates.id'), nullable=False)
    gate = relationship("Gate", back_populates="cameras")
    # client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    # client = relationship('Client', back_populates='cameras')
    settings = relationship("CameraSetting", secondary=camera_settings_association, back_populates="cameras", lazy="joined")
    clients = relationship(
            'Client',
            secondary=client_camera_association,
            back_populates='cameras'
        )
