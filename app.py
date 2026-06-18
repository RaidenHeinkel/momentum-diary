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
if 'current_page' not in st.session_state:
    st.session_state.current_page = "calendar"
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
if 'edit_date' not in st.session_state:
    st.session_state.edit_date = ""
if 'edit_header' not in st.session_state:
    st.session_state.edit_header = ""
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# --- 💾 共通の保存通信関数 ---
def save_diary(date_str, header_str, content_str):
    payload = {"date": date_str, "header": header_str, "content": content_str}
    try:
        res = requests.post(GAS_URL, json=payload)
        if res.status_code == 200:
            st.session_state.local_updates[date_str] = content_str
            return True
    except:
        pass
    return False

def save_current_diary_if_changed():
    if st.session_state.previous_date:
        prev_key = f"diary_content_{st.session_state.previous_date}"
        if prev_key in st.session_state:
            current_input = st.session_state[prev_key]
            if current_input != st.session_state.local_updates.get(st.session_state.previous_date, "__NOT_SET__"):
                p_date = datetime.datetime.strptime(st.session_state.previous_date, "%Y-%m-%d").date()
                weekdays = ["月", "火", "水", "木", "金", "土", "日"]
                p_header = f"{p_date.year}年{p_date.month}月{p_date.day}日（{weekdays[p_date.weekday()]}）"
                save_diary(st.session_state.previous_date, p_header, current_input)

# データの先読み
df_all = get_data(SHEET_URL)
existing_dates = set(df_all[df_all['content'].str.strip() != '']['date'].tolist())

# --- CSSスタイル定義 ---
st.markdown("""
<style>
.main .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
.responsive-title { font-size: 1.6rem !important; font-weight: bold; text-align: center; margin-bottom: 8px !important; }
div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; width: 100% !important; gap: 2px !important; }
div[data-testid="stColumn"], div[data-testid="column"] { width: 0 !important; flex-grow: 1 !important; flex-shrink: 1 !important; flex-basis: 0% !important; min-width: 0 !important; padding: 0 !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 画面１：カレンダー画面
# =====================================================================
if st.session_state.current_page == "calendar":
    st.markdown("""
    <style>
    .stButton > button { width: 100% !important; padding: 0.4rem 0 !important; font-size: 0.75rem !important; margin: 0 !important; }
    .weekday-header { text-align: center; font-size: 0.75rem; font-weight: bold; color: #888888; margin: 0 0 3px 0; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)
    col_prev_year, col_year_select, col_next_year = st.columns([1, 2, 1])
    if col_prev_year.button("⏪ 前年"): save_current_diary_if_changed(); st.session_state.view_year -= 1; st.rerun()
    year_options = list(range(st.session_state.view_year - 10, st.session_state.view_year + 11))
    selected_year = col_year_select.selectbox("年選択", options=year_options, index=year_options.index(st.session_state.view_year), label_visibility="collapsed")
    if selected_year != st.session_state.view_year: save_current_diary_if_changed(); st.session_state.view_year = selected_year; st.rerun()
    if col_next_year.button("翌年 ⏩"): save_current_diary_if_changed(); st.session_state.view_year += 1; st.rerun()
    
    col_prev_month, col_today, col_next_month = st.columns(3)
    if col_prev_month.button("◀ 前月"): save_current_diary_if_changed(); st.session_state.view_month = 12 if st.session_state.view_month == 1 else st.session_state.view_month - 1; st.session_state.view_year -= 1 if st.session_state.view_month == 12 else 0; st.rerun()
    if col_today.button("Today"): save_current_diary_if_changed(); today = datetime.date.today(); st.session_state.selected_date = today; st.session_state.view_year = today.year; st.session_state.view_month = today.month; st.rerun()
    if col_next_month.button("翌月 ▶"): save_current_diary_if_changed(); st.session_state.view_month = 1 if st.session_state.view_month == 12 else st.session_state.view_month + 1; st.session_state.view_year += 1 if st.session_state.view_month == 1 else 0; st.rerun()

    st.markdown(f"<h4 style='text-align: center; margin: 8px 0; font-size: 1rem;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h4>", unsafe_allow_html=True)
    cols_header = st.columns(7)
    for i, w in enumerate(["月", "火", "水", "木", "金", "土", "日"]): cols_header[i].markdown(f"<p class='weekday-header'>{w}</p>", unsafe_allow_html=True)
    for week in calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month):
        cols_days = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                d_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
                is_sel = (st.session_state.selected_date == datetime.date(st.session_state.view_year, st.session_state.view_month, day))
                if cols_days[i].button(f"🔹{day}" if d_str in existing_dates else str(day), type="primary" if is_sel else "secondary", use_container_width=True):
                    save_current_diary_if_changed(); st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day); st.rerun()

    d_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    header_str = f"{st.session_state.selected_date.year}年{st.session_state.selected_date.month}月{st.session_state.selected_date.day}日（{['月', '火', '水', '木', '金', '土', '日'][st.session_state.selected_date.weekday()]}）"
    st.markdown(f"<p style='font-size: 0.95rem; font-weight: bold;'>{header_str}</p>", unsafe_allow_html=True)
    content_key = f"diary_content_{d_str}"
    if st.session_state.previous_date != d_str:
        df = get_data(SHEET_URL); st.session_state[content_key] = st.session_state.local_updates.get(d_str, df[df['date'] == d_str]['content'].values[0] if not df[df['date'] == d_str].empty else ""); st.session_state.previous_date = d_str
    content = st.text_area("", key=content_key, height=180)
    c1, c2, c3 = st.columns([3, 1, 1])
    if c1.button("保存", type="primary", use_container_width=True): save_diary(d_str, header_str, content); st.rerun()
    if c2.button("🔄", use_container_width=True): st.cache_data.clear(); st.rerun()
    if c3.button("📊", use_container_width=True): save_current_diary_if_changed(); st.session_state.current_page = "list"; st.rerun()

# =====================================================================
# 画面２：一覧画面
# =====================================================================
elif st.session_state.current_page == "list":
    st.markdown("""<style>.stButton > button { height: auto !important; min-height: 4.5rem; text-align: left !important; width: 100% !important; } .stButton > button * { text-align: left !important; } </style>""", unsafe_allow_html=True)
    df_list = get_data(SHEET_URL)
    for d, c in st.session_state.local_updates.items():
        if d in df_list['date'].values: df_list.loc[df_list['date'] == d, 'content'] = c
    df_list = df_list[df_list['content'].str.strip() != ''].sort_values(by='date', ascending=False)

    col_back, col_title = st.columns([1.3, 4.7])
    # メインに戻るときに検索クエリをクリア
    if col_back.button("⬅️ 戻る", use_container_width=True): st.session_state.search_query = ""; st.session_state.current_page = "calendar"; st.rerun()

    def update_search():
        st.session_state.search_query = st.session_state.temp_search
    
    q_col, c_col = st.columns([4, 1])
    q_col.text_input("", value=st.session_state.search_query, key="temp_search", placeholder="🔍 キーワード検索...", on_change=update_search, label_visibility="collapsed")
    if c_col.button("クリア", use_container_width=True): st.session_state.search_query = ""; st.session_state.temp_search = ""; st.rerun()

    if st.session_state.search_query:
        df_list = df_list[df_list['content'].str.contains(st.session_state.search_query, case=False, na=False) | df_list['date'].str.contains(st.session_state.search_query, na=False)]
    
    col_title.markdown(f"<p style='margin:0; padding-top:6px; font-weight:bold;'>📊 {len(df_list)}件</p>", unsafe_allow_html=True)
    with st.container(height=520):
        for idx, row in df_list.iterrows():
            if st.button(f"📅 {row['date']}\n{row['content'][:50]}", key=f"l_{idx}"):
                st.session_state.edit_date = row['date']; st.session_state.edit_header = row['header']; st.session_state.current_page = "edit"; st.rerun()

# =====================================================================
# 画面３：編集画面
# =====================================================================
elif st.session_state.current_page == "edit":
    if st.button("⬅️ 戻る"): st.session_state.current_page = "list"; st.rerun()
    df = get_data(SHEET_URL)
    val = st.session_state.local_updates.get(st.session_state.edit_date, df[df['date'] == st.session_state.edit_date]['content'].values[0] if not df[df['date'] == st.session_state.edit_date].empty else "")
    new_c = st.text_area("内容", value=val, height=360)
    if st.button("💾 保存", type="primary", use_container_width=True):
        if save_diary(st.session_state.edit_date, st.session_state.edit_header, new_c): st.session_state.current_page = "list"; st.rerun()
