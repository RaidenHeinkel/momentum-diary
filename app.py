import streamlit as st
import requests
import pandas as pd
import datetime

# 設定：GASのURLとスプレッドシートの公開CSV URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- データ読み込み ---
@st.cache_data(ttl=1)
def get_data():
    return pd.read_csv(SHEET_URL).fillna("")

df = get_data()

# --- サイドバー (メニュー) ---
st.sidebar.title("Momentum Diary")

# 今日へジャンプするボタン
if st.sidebar.button("Today"):
    st.session_state.selected_date = datetime.date.today()

# カレンダー選択
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

selected_date = st.sidebar.date_input("日付を選択", value=st.session_state.selected_date)
st.session_state.selected_date = selected_date

# --- メインエリア ---
date_str = selected_date.strftime("%Y-%m-%d")
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
header_str = f"{selected_date.year}年{selected_date.month}月{selected_date.day}日（{weekdays[selected_date.weekday()]}）"

st.subheader(header_str)

# 【修正ポイント】日付が切り替わったときだけ、スプレッドシートからデータを読み込む
if 'previous_date' not in st.session_state or st.session_state.previous_date != date_str:
    st.session_state.previous_date = date_str
    entry = df[df['date'] == date_str]
    # 最初に見つかったデータをセッションに一時保存
    st.session_state.current_diary_content = entry['content'].values[0] if not entry.empty else ""

# 入力エリア（keyを使ってセッション状態と直接連動させます）
content = st.text_area("日記本文", key="current_diary_content", height=300)

# 保存処理
if st.button("保存"):
    payload = {"date": date_str, "header": header_str, "content": content}
    response = requests.post(GAS_URL, json=payload)
    if response.status_code == 200:
        st.success("保存しました！")
        st.rerun()
    else:
        st.error("保存に失敗しました")
