from sqlalchemy.orm import Session
from . import models
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import and_

def create_restaurant(db: Session, **kwargs):
    r = models.Restaurant(**kwargs)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

def list_restaurants(db: Session, city: str = None, cuisine: str = None, limit: int = 10):
    q = db.query(models.Restaurant)
    if city:
        q = q.filter(models.Restaurant.city.ilike(f"%{city}%"))
    if cuisine:
        q = q.filter(models.Restaurant.cuisine.ilike(f"%{cuisine}%"))
    return q.limit(limit).all()

def check_availability(db: Session, restaurant_id: int, party_size: int, desired_time: datetime, slot_minutes=120):
    # naive availability: count all reservations overlapping desired slot and compare to capacity
    r = db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()
    if not r:
        return {"available": False, "reason": "Restaurant not found"}
    start = desired_time
    end = desired_time + timedelta(minutes=slot_minutes)
    overlapping = db.query(models.Reservation).filter(
        models.Reservation.restaurant_id == restaurant_id,
        models.Reservation.status != "CANCELLED",
        and_(
            models.Reservation.time_from < end,
            (models.Reservation.time_to == None) | (models.Reservation.time_to > start)
        )
    ).count()
    # For simplicity assuming each reservation occupies average seats = party_size,
    # and capacity is total seats. A production system needs table layout.
    # Here I estimate used seats = sum of party_size of overlapping reservations
    used_seats = sum([res.party_size for res in db.query(models.Reservation).filter(
        models.Reservation.restaurant_id == restaurant_id,
        models.Reservation.status != "CANCELLED",
        and_(
            models.Reservation.time_from < end,
            (models.Reservation.time_to == None) | (models.Reservation.time_to > start)
        )
    ).all()]) or 0
    available_seats = r.capacity - used_seats
    return {"available": available_seats >= party_size, "available_seats": available_seats, "capacity": r.capacity}

def create_user_if_not_exists(db: Session, name: str, phone: str, email: str = None):
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if user:
        return user
    user = models.User(name=name, phone=phone, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_reservation(db: Session, restaurant_id: int, user_name: str, phone: str, party_size:int, time_from: datetime, time_to: datetime = None):
    user = create_user_if_not_exists(db, user_name, phone)
    res = models.Reservation(
        restaurant_id=restaurant_id, user_id=user.id, user_name=user_name,
        phone=phone, party_size=party_size, time_from=time_from,
        time_to=time_to or (time_from + timedelta(hours=2)),
        status="CONFIRMED"
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

def get_reservation(db: Session, reservation_id: int):
    return db.query(models.Reservation).filter(models.Reservation.id==reservation_id).first()

def cancel_reservation(db: Session, reservation_id: int):
    r = get_reservation(db, reservation_id)
    if not r:
        return {"ok": False, "reason": "not_found"}
    r.status = "CANCELLED"
    db.commit()
    return {"ok": True}
