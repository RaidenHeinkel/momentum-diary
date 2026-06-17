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

# 【修正ポイント①】アプリ内での最新保存履歴（ローカル記憶）を初期化
if 'local_updates' not in st.session_state:
    st.session_state.local_updates = {}

# --- サイドバー (メニュー) ---
st.sidebar.title("Momentum Diary")

if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# 今日へジャンプするボタン
if st.sidebar.button("Today"):
    st.session_state.selected_date = datetime.date.today()
    st.rerun()

# カレンダー選択
selected_date = st.sidebar.date_input("日付を選択", key="selected_date")

# --- メインエリア ---
date_str = selected_date.strftime("%Y-%m-%d")
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
header_str = f"{selected_date.year}年{selected_date.month}月{selected_date.day}日（{weekdays[selected_date.weekday()]}）"

st.subheader(header_str)

# 【修正ポイント②】入力エリアのキーを日付ごとに完全分離（混線バグを防止）
content_key = f"diary_content_{date_str}"

# この日付のデータが未読込の場合のみ処理
if content_key not in st.session_state:
    # まず、Googleのタイムラグに影響されない「アプリ独自のローカル記憶」をチェック
    if date_str in st.session_state.local_updates:
        st.session_state[content_key] = st.session_state.local_updates[date_str]
    else:
        # ローカルに記憶がなければ、スプレッドシート（CSV）から読み込む
        entry = df[df['date'] == date_str]
        st.session_state[content_key] = entry['content'].values[0] if not entry.empty else ""

# 入力エリア
content = st.text_area("日記本文", key=content_key, height=300)

# 保存処理
if st.button("保存"):
    payload = {"date": date_str, "header": header_str, "content": content}
    response = requests.post(GAS_URL, json=payload)
    if response.status_code == 200:
        # 【修正ポイント③】保存した内容（空っぽにしたなら空欄）を即座にローカル記憶に保存
        st.session_state.local_updates[date_str] = content
        st.success("保存しました！")
        st.rerun()
    else:
        st.error("保存に失敗しました")
