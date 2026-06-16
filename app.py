import streamlit as st
import requests
import pandas as pd
import datetime

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbyJtg-SZVpFnUUMxkJ1PkEUqHVOrBAjWhoK7xGQQFgEsniRMLMf6YDI5H2x2ORhZL1rYA/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- データの再読み込み ---
def fetch_data():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except:
        return pd.DataFrame(columns=['date', 'header', 'content'])

# --- 自動保存 ---
def save_data():
    payload = {
        "date": st.session_state.selected_date.strftime("%Y-%m-%d"),
        "header": str(st.session_state.selected_date),
        "content": st.session_state.diary_text
    }
    requests.post(GAS_URL, json=payload)

# --- メインロジック ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

st.title("Momentum Diary")

# 日付選択
st.session_state.selected_date = st.date_input("日付", value=st.session_state.selected_date)

# データ取得
df = fetch_data()
entry = df[df['date'] == st.session_state.selected_date.strftime("%Y-%m-%d")]
initial_text = entry['content'].values[0] if not entry.empty else ""

# 入力エリア
st.text_area("本文", value=initial_text, key="diary_text", height=400, on_change=save_data)

if st.button("リロード（最新データ取得）"):
    st.rerun()
