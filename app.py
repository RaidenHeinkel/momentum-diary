import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# 設定：GASとスプレッドシートのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lXoSqz_TNSuzKpnNOrytNJ5P6uc-Wjr3Q2Bp1-A0Fxk/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- 共通関数 ---
@st.cache_data(ttl=0)
def get_data(url):
    df = pd.read_csv(url).fillna("")
    valid_rows = []
    for _, row in df.iterrows():
        try:
            if str(row['date']).strip() == "": continue
            datetime.datetime.strptime(str(row['date']).strip(), "%Y-%m-%d")
            valid_rows.append(row)
        except: continue
    return pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)

def save_diary(date_str, header_str, content_str):
    try:
        res = requests.post(GAS_URL, json={"date": date_str, "header": header_str, "content": content_str})
        if res.status_code == 200:
            st.session_state.local_updates[date_str] = content_str
            return True
    except: pass
    return False

# --- 状態の初期化 ---
if 'current_page' not in st.session_state: st.session_state.current_page = "calendar"
if 'selected_date' not in st.session_state: st.session_state.selected_date = datetime.date.today()
if 'view_year' not in st.session_state: st.session_state.view_year = st.session_state.selected_date.year
if 'view_month' not in st.session_state: st.session_state.view_month = st.session_state.selected_date.month
if 'previous_date' not in st.session_state: st.session_state.previous_date = None
if 'local_updates' not in st.session_state: st.session_state.local_updates = {}
if 'search_query' not in st.session_state: st.session_state.search_query = ""

# --- CSS ---
st.markdown("""<style>.responsive-title { font-size: 1.6rem !important; font-weight: bold; text-align: center; } 
div[data-testid="stColumn"] { padding: 0 !important; } .stButton > button { width: 100% !important; }</style>""", unsafe_allow_html=True)

# =====================================================================
# 1. カレンダー画面
# =====================================================================
if st.session_state.current_page == "calendar":
    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⏪"): st.session_state.view_year -= 1; st.rerun()
    st.session_state.view_year = c2.selectbox("", list(range(2020, 2030)), index=list(range(2020, 2030)).index(st.session_state.view_year), label_visibility="collapsed")
    if c3.button("⏩"): st.session_state.view_year += 1; st.rerun()

    cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                d_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
                if cols[i].button(str(day)): st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day); st.rerun()

    d_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    content_key = f"c_{d_str}"
    if content_key not in st.session_state: st.session_state[content_key] = get_data(SHEET_URL)[get_data(SHEET_URL)['date'] == d_str]['content'].values[0] if not get_data(SHEET_URL)[get_data(SHEET_URL)['date'] == d_str].empty else ""
    
    content = st.text_area("", key=content_key)
    if st.button("保存"): save_diary(d_str, d_str, content); st.rerun()
    if st.button("一覧へ"): st.session_state.current_page = "list"; st.rerun()

# =====================================================================
# 2. 一覧画面（検索・戻る保持）
# =====================================================================
elif st.session_state.current_page == "list":
    if st.button("⬅️ 戻る"): st.session_state.current_page = "calendar"; st.rerun()
    
    col1, col2 = st.columns([4, 1])
    st.session_state.search_query = col1.text_input("検索", value=st.session_state.search_query, placeholder="キーワード...")
    if col2.button("クリア"): st.session_state.search_query = ""; st.rerun()
    
    df = get_data(SHEET_URL)
    if st.session_state.search_query:
        df = df[df['content'].str.contains(st.session_state.search_query, case=False, na=False)]
    
    for _, row in df.iterrows():
        if st.button(f"{row['date']}: {row['content'][:20]}"):
            st.session_state.edit_date = row['date']; st.session_state.current_page = "edit"; st.rerun()

# =====================================================================
# 3. 編集画面
# =====================================================================
elif st.session_state.current_page == "edit":
    ed = st.session_state.edit_date
    if st.button("⬅️ 戻る"): st.session_state.current_page = "list"; st.rerun()
    val = get_data(SHEET_URL)[get_data(SHEET_URL)['date'] == ed]['content'].values[0]
    new_c = st.text_area("編集", value=val)
    if st.button("💾 保存"): save_diary(ed, ed, new_c); st.session_state.current_page = "list"; st.rerun()
