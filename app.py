import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# 設定：GASのURLとスプレッドシートの公開CSV URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- 【超重要】スマホの画面幅に絶対収めるための新CSS ---
st.markdown("""
<style>
/* タイトルの文字サイズをスマホ向けに最適化して改行を防ぐ */
.responsive-title {
    font-size: 1.8rem !important;
    font-weight: bold;
    text-align: center;
    margin-bottom: 15px;
}
/* 列の親要素：横並びを固定し、はみ出しを防ぐ */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    gap: 4px !important;
}
/* 列の子要素：Streamlitの「幅100%」を解除し、均等に分配する */
div[data-testid="column"] {
    width: auto !important; /* スマホ用の100%幅を無効化 */
    flex: 1 1 0% !important; /* 3列なら1/3、7列なら1/7に自動均等割り */
    min-width: 0 !important;
    padding: 0 !important;
}
/* カレンダーボタン：スマホの幅に合わせて文字や余白を極小化 */
.stButton > button {
    width: 100% !important;
    padding: 0.4rem 0 !important;
    font-size: 0.8rem !important;
    margin: 0 !important;
}
/* 曜日ヘッダー */
.weekday-header {
    text-align: center;
    font-size: 0.75rem;
    font-weight: bold;
    color: #888888;
    margin: 0 0 5px 0;
}
</style>
""", unsafe_allow_html=True)

# --- データ読み込み ---
@st.cache_data(ttl=1)
def get_data():
    return pd.read_csv(SHEET_URL).fillna("")

df = get_data()

if 'local_updates' not in st.session_state:
    st.session_state.local_updates = {}

# --- 日付状態の初期化 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

if 'view_year' not in st.session_state:
    st.session_state.view_year = st.session_state.selected_date.year
if 'view_month' not in st.session_state:
    st.session_state.view_month = st.session_state.selected_date.month

# --- メインエリア UI ---
# タイトルをレスポンシブ化
st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)

# 1. カレンダー操作ボタン（これでスマホでも綺麗に3等分されます）
col_prev, col_today, col_next = st.columns(3)
if col_prev.button("◀ 前月", use_container_width=True):
    if st.session_state.view_month == 1:
        st.session_state.view_month = 12
        st.session_state.view_year -= 1
    else:
        st.session_state.view_month -= 1
    st.rerun()

if col_today.button("Today", use_container_width=True):
    today = datetime.date.today()
    st.session_state.selected_date = today
    st.session_state.view_year = today.year
    st.session_state.view_month = today.month
    st.rerun()

if col_next.button("翌月 ▶", use_container_width=True):
    if st.session_state.view_month == 12:
        st.session_state.view_month = 1
        st.session_state.view_year += 1
    else:
        st.session_state.view_month += 1
    st.rerun()

# 現在の表示年月
st.markdown(f"<h4 style='text-align: center; margin: 10px 0; font-size: 1.1rem;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h4>", unsafe_allow_html=True)

# 2. 曜日ヘッダーの表示（綺麗に7等分されます）
weekdays_headers = ["月", "火", "水", "木", "金", "土", "日"]
cols_header = st.columns(7)
for i, w in enumerate(weekdays_headers):
    cols_header[i].markdown(f"<p class='weekday-header'>{w}</p>", unsafe_allow_html=True)

# 3. 埋め込みカレンダー本体（綺麗に7等分されます）
cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
for week in cal:
    cols_days = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols_days[i].write("")  # 空白マス
        else:
            is_selected = (
                st.session_state.selected_date.year == st.session_state.view_year and
                st.session_state.selected_date.month == st.session_state.view_month and
                st.session_state.selected_date.day == day
            )
            btn_type = "primary" if is_selected else "secondary"
            
            if cols_days[i].button(
                str(day), 
                key=f"btn_{st.session_state.view_year}_{st.session_state.view_month}_{day}", 
                type=btn_type, 
                use_container_width=True
            ):
                st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                st.rerun()

st.markdown("---")

# 4. 日記入力セクション
selected_date = st.session_state.selected_date
date_str = selected_date.strftime("%Y-%m-%d")
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
header_str = f"{selected_date.year}年{selected_date.month}月{selected_date.day}日（{weekdays[selected_date.weekday()]}）"

st.subheader(header_str)

content_key = f"diary_content_{date_str}"

if content_key not in st.session_state:
    if date_str in st.session_state.local_updates:
        st.session_state[content_key] = st.session_state.local_updates[date_str]
    else:
        entry = df[df['date'] == date_str]
        st.session_state[content_key] = entry['content'].values[0] if not entry.empty else ""

content = st.text_area("日記本文", key=content_key, height=220)

# 保存処理
if st.button("保存", use_container_width=True):
    payload = {"date": date_str, "header": header_str, "content": content}
    response = requests.post(GAS_URL, json=payload)
    if response.status_code == 200:
        st.session_state.local_updates[date_str] = content
        st.success("保存しました！")
        st.rerun()
    else:
        st.error("保存に失敗しました")
