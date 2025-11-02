from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, index=True)
    address = Column(Text)
    cuisine = Column(String, index=True)
    capacity = Column(Integer, default=50)
    avg_price = Column(Float, default=1000.0)
    tags = Column(String)
    open_hours = Column(String)  # simple text like "10:00-23:00"

    reservations = relationship("Reservation", back_populates="restaurant")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String, unique=True, index=True)
    email = Column(String, unique=True, nullable=True)

    reservations = relationship("Reservation", back_populates="user")

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String)
    phone = Column(String)
    party_size = Column(Integer)
    time_from = Column(DateTime)
    time_to = Column(DateTime, nullable=True)
    status = Column(String, default="CONFIRMED")
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="reservations")
    user = relationship("User", back_populates="reservations")
