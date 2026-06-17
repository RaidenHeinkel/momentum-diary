import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# 設定：GASのURLとスプレッドシートの公開CSV URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"

# スマホ向けに中央寄せのコンパクトレイアウトに設定
st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- 【スマホ最適化】CSSの注入 ---
st.markdown("""
<style>
/* スマホの狭い画面でも、columns（列）が縦に回り込んで崩れるのを強制防止 */
div[data-testid="stHorizontalBlock"] {
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 4px !important;
}
div[data-testid="column"] {
    min-width: 0 !important;
    flex-grow: 1 !important;
    padding: 0 !important;
}
/* カレンダーの数字ボタンをスマホの指でタップしやすく、かつコンパクトに */
.stButton > button {
    width: 100% !important;
    padding: 0.5rem 0.2rem !important;
    font-size: 0.9rem !important;
    margin: 0 !important;
}
/* 曜日ヘッダーのデザインをスマホ用に微調整 */
.weekday-header {
    text-align: center;
    font-size: 0.8rem;
    font-weight: bold;
    color: #888888;
    margin: 0 0 5px 0;
}
</style>
""", unsafe_allow_html=True)

# --- 数据読み込み ---
@st.cache_data(ttl=1)
def get_data():
    return pd.read_csv(SHEET_URL).fillna("")

df = get_data()

# アプリ内での最新保存履歴（ローカル記憶）を初期化
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
st.title("Momentum Diary")

# 1. カレンダー操作ボタン（前月・Today・翌月を横一列にスッキリ配置）
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
st.markdown(f"<h4 style='text-align: center; margin: 10px 0;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h4>", unsafe_allow_html=True)

# 2. 曜日ヘッダーの表示
weekdays_headers = ["月", "火", "水", "木", "金", "土", "日"]
cols_header = st.columns(7)
for i, w in enumerate(weekdays_headers):
    cols_header[i].markdown(f"<p class='weekday-header'>{w}</p>", unsafe_allow_html=True)

# 3. 埋め込みカレンダー本体
cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
for week in cal:
    cols_days = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols_days[i].write("")  # 月の枠外（空白）
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

# 入力エリア（高さもスマホで見やすいサイズに調整）
content = st.text_area("日記本文", key=content_key, height=250)

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
