from .llm_interface import query_llm_json
from db.db import SessionLocal, engine
from . import crud, models
from datetime import datetime
import json

# helper: ensure DB tables exist (call once)
def ensure_db():
    models.Base.metadata.create_all(bind=engine)

ensure_db()

# SYSTEM_PROMPT = """
# You are GoodFoods Assistant. When ready to take an action you MUST output JSON exactly matching one of the following shapes (no extra commentary):

# - search_restaurants: {"action": "search_restaurants", "params": {"city": "...", "cuisine": "...", "party_size": 4, "time": "2025-11-30T19:00"}}
# - check_availability: {"action": "check_availability", "params": {"restaurant_id": 12, "party_size": 4, "time": "2025-11-30T19:00"}}
# - create_reservation: {"action": "create_reservation", "params": {"restaurant_id": 12, "user_name": "Aditi", "phone": "+911234567890", "party_size": 4, "time": "2025-11-30T19:00"}}
# - cancel_reservation: {"action": "cancel_reservation", "params": {"reservation_id": 123}}

# If you need more information, respond in plain text asking for the specific missing field(s).
# """

SYSTEM_PROMPT = """
You are GoodFoods Reservation Assistant.

Your job:
- Understand the user’s intent (search, book, cancel, check availability)
- Output only valid JSON following this schema:
{
  "action": "<action_name>",
  "params": {
    "city": "<city name>",
    "cuisine": "<cuisine>",
    "party_size": <int>,
    "time": "<HH:MM or empty>",
    "user_name": "<optional>",
    "phone": "<optional>",
    "restaurant_id": "<optional>",
    "reservation_id": "<optional>"
  }
}

Strict Rules:
1. Do not include explanations or text outside JSON.
2. Always return JSON — even if some fields are unknown, keep them empty.
3. Examples:
User: I want to book an Italian restaurant in Delhi.
Assistant:
{"action": "search_restaurants", "params": {"city": "Delhi", "cuisine": "Italian", "party_size": "", "time": ""}}
"""


def call_tools_from_user_message(user_message: str):
    # ask the model to produce an action JSON or a clarification
    prompt = SYSTEM_PROMPT + "\n\nUser: " + user_message + "\n\nAssistant:"
    parsed = query_llm_json(prompt)
    # if parsed contains 'raw', return the raw for human-style prompt back
    if parsed is None:
        return {"error": "no_response"}
    if 'raw' in parsed:
        # LLM didn't yield JSON — return the text to front-end
        return {"text": parsed['raw']}
    elif "action" in parsed:
        # Optional natural-language preview before DB call
        preview = format_user_response(parsed)
    action = parsed.get("action")
    params = parsed.get("params", {})
    # open DB session and dispatch
    db = SessionLocal()
    try:
        if action == "search_restaurants":
            city = params.get("city")
            cuisine = params.get("cuisine")
            limit = params.get("limit", 6)
            results = crud.list_restaurants(db, city=city, cuisine=cuisine, limit=limit)
            # convert to serializable
            out = [{"id": r.id, "name": r.name, "city": r.city, "cuisine": r.cuisine, "capacity": r.capacity, "avg_price": r.avg_price, "tags": r.tags} for r in results]
            return {"action": action, "results": out}
        elif action == "check_availability":
            rid = int(params.get("restaurant_id"))
            party_size = int(params.get("party_size", 2))
            time_s = params.get("time")
            desired_time = datetime.fromisoformat(time_s)
            info = crud.check_availability(db, rid, party_size, desired_time)
            return {"action": action, "result": info}
        elif action == "create_reservation":
            rid = int(params.get("restaurant_id"))
            name = params.get("user_name", "Guest")
            phone = params.get("phone")
            party_size = int(params.get("party_size", 2))
            time_s = params.get("time")
            desired_time = datetime.fromisoformat(time_s)
            res = crud.create_reservation(db, rid, name, phone, party_size, desired_time)
            return {"action": action, "reservation_id": res.id, "status": res.status}
        elif action == "cancel_reservation":
            rid = int(params.get("reservation_id"))
            ok = crud.cancel_reservation(db, rid)
            return {"action": action, "result": ok}
        else:
            return {"error": "unknown_action", "parsed": parsed}
    finally:
        db.close()

def format_user_response(parsed):
    if "action" not in parsed:
        return "Sorry, I didn’t quite get that."
    action = parsed.get("action")
    params = parsed.get("params", {})
    if action == "search_restaurants":
        return f"Sure — looking for {params.get('cuisine','')} restaurants in {params.get('city','')}."
    elif action == "create_reservation":
        return f"Got it! Booking your table at restaurant ID {params.get('restaurant_id')} for {params.get('party_size')} people."
    elif action == "check_availability":
        return f"Checking availability for restaurant {params.get('restaurant_id')}..."
    elif action == "cancel_reservation":
        return f"Okay, cancelling reservation {params.get('reservation_id')}."
    else:
        return "I'm ready to help with your reservation!"
