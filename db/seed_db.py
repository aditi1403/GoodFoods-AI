import os
import random
from faker import Faker
from datetime import time
from db.db import engine, SessionLocal
from backend import models, crud

def seed_restaurants(n=100):
    fake = Faker()
    cuisines = ["Indian", "Italian", "Chinese", "Thai", "Mexican", "Continental", "Japanese"]
    cities = ["Bangalore", "Delhi", "Mumbai", "Kolkata", "Chennai", "Hyderabad", "Pune"]
    session = SessionLocal()
    models.Base.metadata.create_all(bind=engine)
    # optional: wipe restaurants
    session.query(models.Reservation).delete()
    session.query(models.Restaurant).delete()
    session.commit()

    for _ in range(n):
        payload = {
            "name": f"{fake.last_name()} {random.choice(['Bistro','Kitchen','Dine','House','Grill','Cafe'])}",
            "city": random.choice(cities),
            "address": fake.address(),
            "cuisine": random.choice(cuisines),
            "capacity": random.randint(20, 120),
            "avg_price": random.choice([400, 600, 900, 1300, 1800]),
            "tags": random.choice(["family", "romantic", "rooftop", "casual", "fine_dining"]),
            "open_hours": "10:00-23:00"
        }
        r = models.Restaurant(**payload)
        session.add(r)
    session.commit()
    print("Seeded", n, "restaurants.")
    # create sample user
    sample_user = models.User(name="Demo User", phone="+911234567890", email="demo@example.com")
    session.add(sample_user)
    session.commit()
    session.close()

if __name__ == "__main__":
    seed_restaurants(100)
