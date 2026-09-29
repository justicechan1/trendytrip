# app/models/jeju_hotel.py
from sqlalchemy import Column, Integer, String, Text, Float, Numeric, BigInteger
from .base import Base

class JejuHotel(Base):
    __tablename__ = "hotel"

    hotel_id    = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=True)
    category    = Column(String(255), nullable=True)
    page_url    = Column(Text, nullable=True)
    score       = Column(Float, nullable=True)
    address     = Column(Text, nullable=True)
    phone       = Column(String(100), nullable=True)
    convenience = Column(Text, nullable=True)
    website     = Column(Text, nullable=True)
    y_cord      = Column(Numeric(10, 7), nullable=True)
    x_cord      = Column(Numeric(10, 7), nullable=True)
    open_time   = Column(String(255), nullable=True)
    close_time  = Column(String(255), nullable=True)
    break_time  = Column(String(255), nullable=True)
    service_time= Column(String(255), nullable=True)
    closed_days = Column(String(255), nullable=True)
    image_url   = Column(Text, nullable=True)
    price       = Column(BigInteger, nullable=True)
    location_code = Column(Integer, nullable=True)
