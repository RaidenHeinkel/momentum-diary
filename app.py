import streamlit as st
import requests
import pandas as pd
import datetime

# 設定：URLはご自身のものに書き換えてください
GAS_URL = "https://script.google.com/macros/s/AKfycbyJtg-SZVpFnUUMxkJ1PkEUqHVOrBAjWhoK7xGQQFgEsniRMLMf6YDI5H2x2ORhZL1rYA/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- データ読み込み ---
@st.cache_data(ttl=1)
def get_data():
    return pd.read_csv(SHEET_URL)

df = get_data()

# --- 自動保存関数 ---
def auto_save():
    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    header_str = f"{st.session_state.selected_date.year}年{st.session_state.selected_date.month}月{st.session_state.selected_date.day}日"
    content = st.session_state.diary_text
    
    payload = {"date": date_str, "header": header_str, "content": content}
    requests.post(GAS_URL, json=payload)
    # 必要に応じてここで st.toast("自動保存しました") を使って通知も出せます

# --- 状態管理 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# --- サイドバー ---
st.sidebar.title("Momentum Diary")
if st.sidebar.button("Today"):
    st.session_state.selected_date = datetime.date.today()
    st.rerun()

new_date = st.sidebar.date_input("日付を選択", value=st.session_state.selected_date)
if new_date != st.session_state.selected_date:
    st.session_state.selected_date = new_date
    st.rerun()

# --- メインエリア ---
date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
entry = df[df['date'] == date_str]
current_content = entry['content'].values[0] if not entry.empty else ""

# テキストエリアの内容が変わるたびに auto_save を実行
st.text_area(
    "日記本文", 
    value=current_content, 
    height=400, 
    key="diary_text", 
    on_change=auto_save
)

st.caption("入力が終わると自動で保存されます")
