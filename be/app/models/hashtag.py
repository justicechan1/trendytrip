# app/models/hashtag.py
from sqlalchemy import Column, Integer, String, JSON, Table, ForeignKey, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from .base import Base

class Hashtag(Base):
    __tablename__ = "hashtag"

    hashtag_id  = Column(Integer, primary_key=True, autoincrement=True)
    hashtag     = Column(String(100), nullable=False, unique=True)
    embeddings  = Column(JSON, nullable=False)  
