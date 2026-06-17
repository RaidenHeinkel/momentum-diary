import streamlit as st
import requests
import pandas as pd
import datetime
import calendar  # 【新機能】カレンダー生成用の標準モジュール

# 設定：GASのURLとスプレッドシートの公開CSV URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- データ読み込み ---
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

# カレンダーの「表示月」を管理するためのセッション状態
if 'view_year' not in st.session_state:
    st.session_state.view_year = st.session_state.selected_date.year
if 'view_month' not in st.session_state:
    st.session_state.view_month = st.session_state.selected_date.month

# --- サイドバー (メニュー) ---
st.sidebar.title("Momentum Diary")

# 今日へジャンプするボタン（カレンダーの表示月も一緒にリセットします）
if st.sidebar.button("Today", use_container_width=True):
    today = datetime.date.today()
    st.session_state.selected_date = today
    st.session_state.view_year = today.year
    st.session_state.view_month = today.month
    st.rerun()

st.sidebar.markdown("---")

# 【新機能】埋め込みカレンダーUIの構築
# 1. 年月の表示
st.sidebar.markdown(
    f"<h3 style='text-align: center; margin-bottom: 10px;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h3>", 
    unsafe_allow_html=True
)

# 2. 前月・翌月切り替えボタン
col_prev, col_next = st.sidebar.columns(2)
if col_prev.button("◀ 前月", use_container_width=True):
    if st.session_state.view_month == 1:
        st.session_state.view_month = 12
        st.session_state.view_year -= 1
    else:
        st.session_state.view_month -= 1
    st.rerun()
if col_next.button("翌月 ▶", use_container_width=True):
    if st.session_state.view_month == 12:
        st.session_state.view_month = 1
        st.session_state.view_year += 1
    else:
        st.session_state.view_month += 1
    st.rerun()

# 3. 曜日ヘッダーの表示
weekdays_headers = ["月", "火", "水", "木", "金", "土", "日"]
cols_header = st.sidebar.columns(7)
for i, w in enumerate(weekdays_headers):
    cols_header[i].markdown(
        f"<p style='text-align: center; font-size: 0.85rem; font-weight: bold; margin: 5px 0;'>{w}</p>", 
        unsafe_allow_html=True
    )

# 4. カレンダーの日にちボタンを7列のグリッドで配置
cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
for week in cal:
    cols_days = st.sidebar.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols_days[i].write("") # 月の枠外（空白マス）
        else:
            # 現在選択されている日付かどうかを判定
            is_selected = (
                st.session_state.selected_date.year == st.session_state.view_year and
                st.session_state.selected_date.month == st.session_state.view_month and
                st.session_state.selected_date.day == day
            )
            
            # 選択中の日だけボタンの色を目立つ色（primary）に変更
            btn_type = "primary" if is_selected else "secondary"
            
            if cols_days[i].button(
                str(day), 
                key=f"btn_{st.session_state.view_year}_{st.session_state.view_month}_{day}", 
                type=btn_type, 
                use_container_width=True
            ):
                # 日付がクリックされたら、選択日を更新して再描画
                st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                st.rerun()

# 最終的に確定した選択日を取得
selected_date = st.session_state.selected_date

# --- メインエリア ---
date_str = selected_date.strftime("%Y-%m-%d")
weekdays = ["月", "火", "水", "木", "金", "土", "日"]
header_str = f"{selected_date.year}年{selected_date.month}月{selected_date.day}日（{weekdays[selected_date.weekday()]}）"

st.subheader(header_str)

# 入力エリアのキーを日付ごとに完全分離
content_key = f"diary_content_{date_str}"

if content_key not in st.session_state:
    if date_str in st.session_state.local_updates:
        st.session_state[content_key] = st.session_state.local_updates[date_str]
    else:
        entry = df[df['date'] == date_str]
        st.session_state[content_key] = entry['content'].values[0] if not entry.empty else ""

# 入力エリア
content = st.text_area("日記本文", key=content_key, height=300)

# 保存処理
if st.button("保存"):
    payload = {"date": date_str, "header": header_str, "content": content}
    response = requests.post(GAS_URL, json=payload)
    if response.status_code == 200:
        st.session_state.local_updates[date_str] = content
        st.success("保存しました！")
        st.rerun()
    else:
        st.error("保存に失敗しました")
