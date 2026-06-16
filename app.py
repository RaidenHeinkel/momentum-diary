import streamlit as st
import requests
import pandas as pd
import datetime

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbyJtg-SZVpFnUUMxkJ1PkEUqHVOrBAjWhoK7xGQQFgEsniRMLMf6YDI5H2x2ORhZL1rYA/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"

st.set_page_config(layout="wide") # 画面を広く使う

# --- データ取得 ---
# キャッシュをクリアして毎回最新を取得
# --- データ取得部分の修正 ---
@st.cache_data(ttl=1)
def get_data():
    # URLが正しい形式か確認し、CSV出力用に強制変換
    url = SHEET_URL.replace("/edit#gid=", "/export?format=csv&gid=")
    try:
        # ヘッダーを明示的に指定して読み込み
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame(columns=['date', 'header', 'content'])

df = get_data()

# --- 状態管理 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# --- 自動保存関数 ---
def auto_save():
    # 入力された内容をGASに送信
    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    content = st.session_state.diary_text
    payload = {"date": date_str, "header": date_str, "content": content}
    requests.post(GAS_URL, json=payload)

# --- UI構築 ---
st.sidebar.title("Momentum Diary")

# カレンダー（date_inputをサイドバーに常駐）
new_date = st.sidebar.date_input("日付を選択", value=st.session_state.selected_date)
if new_date != st.session_state.selected_date:
    st.session_state.selected_date = new_date
    st.rerun()

if st.sidebar.button("Today"):
    st.session_state.selected_date = datetime.date.today()
    st.rerun()

# メインエリア
date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
entry = df[df['date'] == date_str]
current_content = entry['content'].values[0] if not entry.empty else ""

st.subheader(f"{date_str} の日記")
st.text_area("本文", value=current_content, height=400, key="diary_text", on_change=auto_save)
