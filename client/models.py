from sqlalchemy import Column, Enum, Float, Integer, String, ForeignKey, Boolean, DateTime, Text, Table, func
from sqlalchemy import Enum as sqlEnum
from sqlalchemy.orm import relationship
from enum import Enum

from db.engine import Base


class SettingType(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"

client_camera_association = Table(
    'client_camera_association',
    Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('camera_id', Integer, ForeignKey('cameras.id'), primary_key=True)
)


class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ip = Column(String, nullable=False, index=True)
    port = Column(Integer, nullable=False)
    auth_token = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    # Foreign key for LPR
    lpr_id = Column(Integer, ForeignKey('lprs.id'), nullable=False)
    lpr = relationship('LPR', back_populates='clients')

    # Relationship to hold multiple cameras
    cameras = relationship(
            'Camera',
            secondary=client_camera_association,
            back_populates='clients',
            lazy="joined"
        )

class LPR(Base):
    __tablename__ = 'lprs'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    value = Column(String(255), nullable=False)
    type = Column(sqlEnum(SettingType), nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    clients = relationship('Client', back_populates='lpr')
    # gate_id = Column(Integer, ForeignKey('gates.id'), nullable=False)
    # gate = relationship('Gate', back_populates='lprs')


class PlateData(Base):
    __tablename__ = 'plate_data'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # timestamp = Column(String, nullable=False, default=func.now())
    timestamp = Column(DateTime, nullable=False, default=func.now())
    plate_number = Column(String, nullable=False)
    ocr_accuracy = Column(Float, nullable=True)
    vision_speed = Column(Float, nullable=True)
    gate = Column(String, nullable=True)


class ImageData(Base):
    __tablename__ = 'image_data'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_number = Column(String, nullable=False)
    gate = Column(String, nullable=True)
    file_path = Column(String, nullable=False)  # Path to the saved image
    timestamp = Column(DateTime, nullable=False, default=func.now())
