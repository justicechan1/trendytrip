# app/models/hashtag_mapping.py
from sqlalchemy import Column, Integer, ForeignKey, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from .base import Base

# 카페-해시태그 매핑
class CafeHashtagMap(Base):
    __tablename__ = "cafe_hashtag"
    cafe_id    = Column(Integer, ForeignKey("cafe.cafe_id", ondelete="CASCADE"), nullable=False)
    hashtag_id = Column(Integer, ForeignKey("hashtag.hashtag_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("cafe_id", "hashtag_id", name="pk_cafe_hashtag"),
    )

# 호텔-해시태그 매핑
class HotelHashtagMap(Base):
    __tablename__ = "hotel_hashtag"
    hotel_id   = Column(Integer, ForeignKey("hotel.hotel_id", ondelete="CASCADE"), nullable=False)
    hashtag_id = Column(Integer, ForeignKey("hashtag.hashtag_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("hotel_id", "hashtag_id", name="pk_hotel_hashtag"),
    )

# 음식점-해시태그 매핑
class RestaurantHashtagMap(Base):
    __tablename__ = "restaurant_hashtag"
    restaurant_id = Column(Integer, ForeignKey("restaurant.restaurant_id", ondelete="CASCADE"), nullable=False)
    hashtag_id    = Column(Integer, ForeignKey("hashtag.hashtag_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("restaurant_id", "hashtag_id", name="pk_restaurant_hashtag"),
    )

# 관광지-해시태그 매핑
class TourHashtagMap(Base):
    __tablename__ = "tour_hashtag"
    tour_id    = Column(Integer, ForeignKey("tour.tour_id", ondelete="CASCADE"), nullable=False)
    hashtag_id = Column(Integer, ForeignKey("hashtag.hashtag_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("tour_id", "hashtag_id", name="pk_tour_hashtag"),
    )
