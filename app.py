import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# 設定
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lXoSqz_TNSuzKpnNOrytNJ5P6uc-Wjr3Q2Bp1-A0Fxk/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- 共通関数 ---
@st.cache_data(ttl=0)
def get_data(url):
    return pd.read_csv(url).fillna("")

def save_diary(date_str, header_str, content_str):
    payload = {"date": date_str, "header": header_str, "content": content_str}
    try:
        res = requests.post(GAS_URL, json=payload)
        return res.status_code == 200
    except:
        return False

# --- 状態管理 ---
if 'current_page' not in st.session_state: st.session_state.current_page = "calendar"
if 'view_year' not in st.session_state: st.session_state.view_year = datetime.date.today().year
if 'view_month' not in st.session_state: st.session_state.view_month = datetime.date.today().month
if 'search_query' not in st.session_state: st.session_state.search_query = ""

# --- UIコンポーネント: CSS ---
st.markdown("""
<style>
.responsive-title { font-size: 1.5rem !important; font-weight: bold; text-align: center; margin-bottom: 10px; }
.stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 画面構成 ---
def show_calendar():
    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⏪"): st.session_state.view_year -= 1; st.rerun()
    c2.markdown(f"<div style='text-align:center; font-weight:bold;'>{st.session_state.view_year}年</div>", unsafe_allow_html=True)
    if c3.button("⏩"): st.session_state.view_year += 1; st.rerun()

    m1, m2, m3 = st.columns([1, 2, 1])
    if m1.button("◀"):
        st.session_state.view_month -= 1
        if st.session_state.view_month < 1: st.session_state.view_month = 12; st.session_state.view_year -= 1
        st.rerun()
    m2.markdown(f"<div style='text-align:center; font-weight:bold;'>{st.session_state.view_month}月</div>", unsafe_allow_html=True)
    if m3.button("▶"):
        st.session_state.view_month += 1
        if st.session_state.view_month > 12: st.session_state.view_month = 1; st.session_state.view_year += 1
        st.rerun()

    cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                if cols[i].button(str(day)):
                    st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                    st.session_state.current_page = "edit"
                    st.rerun()

    if st.button("一覧を見る"): st.session_state.current_page = "list"; st.rerun()

def show_list():
    st.markdown("## 📊 日記一覧")
    
    # 検索用のコールバック
    def update_search():
        st.session_state.search_query = st.session_state.search_input

    st.text_input("検索", key="search_input", value=st.session_state.search_query, on_change=update_search)
    
    df = get_data(SHEET_URL)
    if st.session_state.search_query:
        df = df[df['content'].str.contains(st.session_state.search_query, na=False)]
    
    for _, row in df.iterrows():
        if st.button(f"{row['date']}: {row['content'][:20]}..."):
            st.session_state.edit_date = row['date']
            st.session_state.current_page = "edit"
            st.rerun()
            
    if st.button("戻る"): st.session_state.current_page = "calendar"; st.rerun()

def show_edit():
    st.write(f"### {st.session_state.get('edit_date', '新規作成')}")
    content = st.text_area("内容")
    if st.button("保存"):
        save_diary(st.session_state.edit_date, "", content)
        st.session_state.current_page = "calendar"
        st.rerun()
    if st.button("キャンセル"): st.session_state.current_page = "calendar"; st.rerun()

# --- ルーティング ---
if st.session_state.current_page == "calendar": show_calendar()
elif st.session_state.current_page == "list": show_list()
elif st.session_state.current_page == "edit": show_edit()
