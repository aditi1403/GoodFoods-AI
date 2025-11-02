import sys, os
import streamlit as st
import requests
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.tools_middleware import call_tools_from_user_message

st.set_page_config(page_title="GoodFoods Chat", layout="wide")
st.title("GoodFoods — Reservation Assistant (POC)")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"assistant","text":"Hi — I'm GoodFoods assistant. How can I help with reservations today?"}]

def post_user_input(text):
    st.session_state.messages.append({"role":"user","text":text})
    # call middleware (local python function)
    result = call_tools_from_user_message(text)
    # present result
    if "text" in result:
        st.session_state.messages.append({"role":"assistant","text": result["text"]})
    elif "action" in result and result["action"] == "search_restaurants":
        # display card list
        items = result.get("results", [])
        if not items:
            st.session_state.messages.append({"role":"assistant","text":"No restaurants found matching your criteria."})
        else:
            txt = "Found restaurants:\n" + "\n".join([f'{it["id"]} - {it["name"]} ({it["cuisine"]}) in {it["city"]} — capacity {it["capacity"]}' for it in items])
            st.session_state.messages.append({"role":"assistant","text": txt })
    elif "action" in result and result["action"] == "create_reservation":
        st.session_state.messages.append({"role":"assistant","text": f"Reservation created (id={result.get('reservation_id')}). Status: {result.get('status')}."})
    elif "action" in result and result["action"] == "check_availability":
        info = result.get("result", {})
        if info.get("available"):
            st.session_state.messages.append({"role":"assistant","text": f"Available — {info.get('available_seats')} seats free."})
        else:
            st.session_state.messages.append({"role":"assistant","text": f"Not available. {info.get('reason','No seats free')}."})
    elif "error" in result:
        st.session_state.messages.append({"role":"assistant","text": f"Error: {result.get('error')} - {result.get('parsed','')}"})
    else:
        st.session_state.messages.append({"role":"assistant","text": str(result)})

# UI
for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(f"**You:** {m['text']}")
    else:
        st.markdown(f"**Assistant:** {m['text']}")

with st.form("input"):
    user_text = st.text_input("Message", "")
    submitted = st.form_submit_button("Send")
    if submitted and user_text:
        post_user_input(user_text)
        st.rerun()
