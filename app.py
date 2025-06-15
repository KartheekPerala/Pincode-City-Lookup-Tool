import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rapidfuzz import process, fuzz
import pandas as pd
import json
from io import StringIO


@st.cache_resource
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1eler29P76woO5wM756lAGk_4cvxoFnFRmlaJG7ZPYrM/edit?gid=973198101#gid=973198101").sheet1
    data = sheet.get_all_records()
    return data

data = load_data()

st.title("Pincode City Lookup Tool")
search_type = st.radio("Search by:", ["Pincode", "City"])
user_input = st.text_input(f"Enter {search_type}:")

if st.button("Search"):
    matches = []

    if search_type == "Pincode":
        search_pincode = user_input.strip()
        matches = [row for row in data if str(row.get("Pincode", "")).strip() == search_pincode]
        if matches:
            st.success("1 match found.")
            df = pd.DataFrame([matches[0]])[["Pincode", "BM", "RM", "ZM"]]
            st.table(df)
        else:
            st.warning("No matching pincode found.")

    elif search_type == "City":
        search_city = user_input.strip().lower()
        city_list = [str(row.get("CITY", "")).strip() for row in data]

        best_match = process.extractOne(search_city, city_list, scorer=fuzz.ratio)
        if best_match and best_match[1] >= 70:
            matched_city = best_match[0]
            st.success(f"Closest match: {matched_city} ({best_match[1]}%)")

            all_rows = [
                row for row in data
                if str(row.get("CITY", "")).strip().lower() == matched_city.lower()
            ]

            seen = set()
            unique_rows = []
            for row in all_rows:
                city = row.get("CITY", "").strip()
                state = row.get("State", "").strip()
                mode = row.get("Sale Mode Allowed", "").strip()
                key = (city, state)
                if key not in seen:
                    seen.add(key)
                    unique_rows.append({
                        "CITY": city,
                        "State": state,
                        "Sale Mode Allowed": mode
                    })

            if unique_rows:
                df = pd.DataFrame(unique_rows)
                st.table(df)
            else:
                st.warning("No matching records found.")
        else:
            st.warning("No close city match found.")
