import streamlit as st
import requests
import datetime

GAS_URL = "https://script.google.com/macros/s/AKfycbz2uCE2r4OLFw0CFIinYPV4JAl2IvZadhOej2vsWMxzpI66pmWhkqWmjaZ6RD1LrcN4Pg/exec" # ※要書き換え

# データ取得（JSON経由）
@st.cache_data(ttl=10)
def get_data():
    try:
        response = requests.get(GAS_URL)
        return response.json()
    except:
        return []

st.title("Momentum Diary")
selected_date = st.date_input("日付", datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")

# データ検索
data = get_data()
initial_text = ""
for item in data:
    if str(item['date']) == date_str:
        initial_text = item['content']
        break

# 自動保存（入力欄）
def update_diary():
    payload = {"date": date_str, "content": st.session_state.text_input}
    requests.post(GAS_URL, json=payload)

st.text_area("本文", value=initial_text, key="text_input", on_change=update_diary, height=400)
