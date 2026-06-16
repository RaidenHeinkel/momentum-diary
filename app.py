import streamlit as st
import requests
import pandas as pd
import datetime

# --- 【必須】ここを書き換えてください ---
GAS_URL = "https://script.google.com/macros/s/AKfycbyJtg-SZVpFnUUMxkJ1PkEUqHVOrBAjWhoK7xGQQFgEsniRMLMf6YDI5H2x2ORhZL1rYA/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"
# --------------------------------------

st.set_page_config(layout="centered")

# --- データ取得 ---
@st.cache_data(ttl=1)
def get_data():
    try:
        # シート全体をCSVとして読み込む
        df = pd.read_csv(SHEET_URL)
        # dateカラムを文字列として扱う（形式不一致防止）
        df['date'] = df['date'].astype(str)
        return df
    except Exception:
        # 読み込めない場合は空の箱を作る
        return pd.DataFrame(columns=['date', 'header', 'content'])

# --- 自動保存関数 ---
def auto_save():
    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    header_str = f"{st.session_state.selected_date.year}年{st.session_state.selected_date.month}月{st.session_state.selected_date.day}日"
    content = st.session_state.diary_text
    
    payload = {"date": date_str, "header": header_str, "content": content}
    try:
        requests.post(GAS_URL, json=payload)
    except:
        pass

# --- UI構築 ---
st.title("Momentum Diary")

# 日付の初期化
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# サイドバーにカレンダーとTodayボタン
st.sidebar.title("メニュー")
new_date = st.sidebar.date_input("日付を選択", value=st.session_state.selected_date)
if new_date != st.session_state.selected_date:
    st.session_state.selected_date = new_date
    st.rerun()

if st.sidebar.button("Today"):
    st.session_state.selected_date = datetime.date.today()
    st.rerun()

# データ読み込みと表示
df = get_data()
date_str = st.session_state.selected_date.strftime("%Y-%m-%d")

# 該当データを検索
entry = df[df['date'] == date_str]
current_content = entry['content'].values[0] if not entry.empty else ""

# 編集エリア（ここに入力すると自動保存が走る）
st.subheader(f"{date_str} の日記")
st.text_area(
    "本文", 
    value=current_content, 
    height=400, 
    key="diary_text", 
    on_change=auto_save
)

st.caption("※入力内容が変更されると自動で保存されます。")
