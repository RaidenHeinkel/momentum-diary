import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# 設定：GASのURLとスプレッドシートのリアルタイムCSV URL
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lXoSqz_TNSuzKpnNOrytNJ5P6uc-Wjr3Q2Bp1-A0Fxk/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- データ読み込み関数 ---
@st.cache_data(ttl=0)
def get_data(url):
    return pd.read_csv(url).fillna("")

# --- 状態の初期化 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()
if 'view_year' not in st.session_state:
    st.session_state.view_year = st.session_state.selected_date.year
if 'view_month' not in st.session_state:
    st.session_state.view_month = st.session_state.selected_date.month
if 'previous_date' not in st.session_state:
    st.session_state.previous_date = None
if 'local_updates' not in st.session_state:
    st.session_state.local_updates = {}

# --- データの先読みと日記あり日付の抽出 ---
df_all = get_data(SHEET_URL)
existing_dates = set(df_all[df_all['content'].str.strip() != '']['date'].tolist())

# --- 💡 iPhone SE2 適合 ＆ 保存インジケーターが見える適正配置CSS ---
st.markdown("""
<style>
/* 1. 外側コンテナの余白調整 */
.stApp { margin-top: 0px !important; padding-top: 0px !important; }
[data-testid="stAppViewContainer"] { padding-top: 0px !important; }

/* 2. 最上部ヘッダーは消す */
[data-testid="stHeader"] { display: none !important; height: 0px !important; }

/* 3. 🛠️ 限界突破の引き上げを「-2.0rem」に緩和！これで保存中マークや通知が画面内にバッチリ復活します */
.main .block-container { 
    padding-top: 0px !important; 
    margin-top: -2.0rem !important; 
    padding-left: 0.5rem !important; 
    padding-right: 0.5rem !important; 
}

/* タイトル余白の調整 */
.responsive-title { 
    font-size: 1.6rem !important; 
    font-weight: bold; 
    text-align: center; 
    margin-top: 0px !important; 
    padding-top: 0px !important;
    margin-bottom: 8px !important; 
}

div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; width: 100% !important; gap: 2px !important; }
div[data-testid="stColumn"], div[data-testid="column"] { width: 0 !important; flex-grow: 1 !important; flex-shrink: 1 !important; flex-basis: 0% !important; min-width: 0 !important; padding: 0 !important; margin: 0 !important; }
.stButton > button { width: 100% !important; padding: 0.4rem 0 !important; font-size: 0.75rem !important; margin: 0 !important; }
.weekday-header { text-align: center; font-size: 0.75rem; font-weight: bold; color: #888888; margin: 0 0 3px 0; }
</style>
""", unsafe_allow_html=True)

# --- メインエリア UI ---
st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)

# 1. カレンダー操作ボタン（2段構成）
col_prev_year, col_next_year = st.columns(2)
if col_prev_year.button("⏪ 前年", use_container_width=True):
    st.session_state.view_year -= 1
    st.rerun()

if col_next_year.button("翌年 ⏩", use_container_width=True):
    st.session_state.view_year += 1
    st.rerun()

st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)

col_prev_month, col_today, col_next_month = st.columns(3)
if col_prev_month.button("◀ 前月", use_container_width=True):
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

if col_next_month.button("翌月 ▶", use_container_width=True):
    if st.session_state.view_month == 12:
        st.session_state.view_month = 1
        st.session_state.view_year += 1
    else:
        st.session_state.view_month += 1
    st.rerun()

# 現在の表示年月
st.markdown(f"<h4 style='text-align: center; margin: 8px 0; font-size: 1rem;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h4>", unsafe_allow_html=True)

# 2. 曜日ヘッダー
weekdays_headers = ["月", "火", "水", "木", "金", "土", "日"]
cols_header = st.columns(7)
for i, w in enumerate(weekdays_headers):
    cols_header[i].markdown(f"<p class='weekday-header'>{w}</p>", unsafe_allow_html=True)

# 3. カレンダー本体
cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
for week in cal:
    cols_days = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols_days[i].write("")
        else:
            current_loop_date_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
            
            is_selected = (
                st.session_state.selected_date.year == st.session_state.view_year and
                st.session_state.selected_date.month == st.session_state.view_month and
                st.session_state.selected_date.day == day
            )
            btn_type = "primary" if is_selected else "secondary"
            
            # 日記データがあるか判定
            has_diary = current_loop_date_str in existing_dates or (
                current_loop_date_str in st.session_state.local_updates and st.session_state.local_updates[current_loop_date_str].strip() != ""
            )
            
            # 💡 日記がある未選択の日には、数字の下にクールなブルーの下線を引くシグナル（文字コード）を付与
            # 特殊な結合用文字を使い、フォントサイズやボタン幅を一切崩さずに表現します
            if has_diary and not is_selected:
                button_label = "".join([c + "\u0332" if c.isdigit() else c for c in str(day)])
            else:
                button_label = str(day)
            
            if cols_days[i].button(button_label, key=f"btn_{st.session_state.view_year}_{st.session_state.view_month}_{day}", type=btn_type, use_container_width=True):
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

if st.session_state.previous_date != date_str or content_key not in st.session_state:
    st.cache_data.clear()
    df = get_data(SHEET_URL)
    
    if date_str in st.session_state.local_updates:
        st.session_state[content_key] = st.session_state.local_updates[date_str]
    else:
        entry = df[df['date'] == date_str]
        st.session_state[content_key] = entry['content'].values[0] if not entry.empty else ""
    
    st.session_state.previous_date = date_str

content = st.text_area("日記本文", key=content_key, height=180)

# ボタンエリア
col_save, col_sync = st.columns([3, 1])

if col_save.button("保存", type="primary", use_container_width=True):
    payload = {"date": date_str, "header": header_str, "content": content}
    # 💡 処理中のインジケーター（右上のRunningグルグルやトースト）がこれでしっかり見えるようになります
    response = requests.post(GAS_URL, json=payload)
    if response.status_code == 200:
        st.session_state.local_updates[date_str] = content
        st.success("保存しました！")
        st.rerun()
    else:
        st.error("保存に失敗しました")

if col_sync.button("🔄 同期", use_container_width=True):
    st.cache_data.clear()
    if content_key in st.session_state:
        del st.session_state[content_key]
    if date_str in st.session_state.local_updates:
        del st.session_state.local_updates[date_str]
    st.rerun()
