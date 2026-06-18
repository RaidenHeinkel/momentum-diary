import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# 設定
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lXoSqz_TNSuzKpnNOrytNJ5P6uc-Wjr3Q2Bp1-A0Fxk/gviz/tq?tqx=out:csv"
SPREADSHEET_VIEW_URL = "https://docs.google.com/spreadsheets/d/1lXoSqz_TNSuzKpnNOrytNJ5P6uc-Wjr3Q2Bp1-A0Fxk/edit"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- データ読み込み（保護機能付き） ---
@st.cache_data(ttl=0)
def get_data(url):
    df = pd.read_csv(url).fillna("")
    valid = []
    for _, row in df.iterrows():
        try:
            if str(row['date']).strip() == "": continue
            datetime.datetime.strptime(str(row['date']).strip(), "%Y-%m-%d")
            valid.append(row)
        except: continue
    return pd.DataFrame(valid) if valid else pd.DataFrame(columns=df.columns)

# --- 状態の初期化 ---
if 'current_page' not in st.session_state: st.session_state.current_page = "calendar"
if 'selected_date' not in st.session_state: st.session_state.selected_date = datetime.date.today()
if 'view_year' not in st.session_state: st.session_state.view_year = st.session_state.selected_date.year
if 'view_month' not in st.session_state: st.session_state.view_month = st.session_state.selected_date.month
if 'previous_date' not in st.session_state: st.session_state.previous_date = None
if 'local_updates' not in st.session_state: st.session_state.local_updates = {}
if 'edit_date' not in st.session_state: st.session_state.edit_date = ""
if 'edit_header' not in st.session_state: st.session_state.edit_header = ""
if 'search_query' not in st.session_state: st.session_state.search_query = ""

# --- 共通関数 ---
def save_diary(date_str, header_str, content_str):
    try:
        res = requests.post(GAS_URL, json={"date": date_str, "header": header_str, "content": content_str})
        if res.status_code == 200: st.session_state.local_updates[date_str] = content_str; return True
    except: pass
    return False

# --- CSS (Python007そのまま) ---
st.markdown("""
<style>
.main .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
.responsive-title { font-size: 1.6rem !important; font-weight: bold; text-align: center; margin-bottom: 8px !important; }
div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; width: 100% !important; gap: 2px !important; }
div[data-testid="stColumn"], div[data-testid="column"] { width: 0 !important; flex-grow: 1 !important; flex-shrink: 1 !important; flex-basis: 0% !important; min-width: 0 !important; padding: 0 !important; margin: 0 !important; }
.stButton > button { width: 100% !important; padding: 0.4rem 0 !important; font-size: 0.75rem !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 1. カレンダー
# =====================================================================
if st.session_state.current_page == "calendar":
    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)
    # (カレンダーの描画部分は変更なし)
    # ... 中略 (以前の007のロジック) ...
    # ※保存・ページ遷移時は以前の通り save_current_diary_if_changed() を呼んでください

# =====================================================================
# 2. 一覧画面（検索・クリア・保持機能）
# =====================================================================
elif st.session_state.current_page == "list":
    c_back, c_title = st.columns([1.3, 4.7])
    if c_back.button("⬅️ 戻る", use_container_width=True): st.session_state.current_page = "calendar"; st.rerun()
    
    # 検索窓とボタン
    q_col, b1_col, b2_col = st.columns([3, 1, 1])
    temp_q = q_col.text_input("", value=st.session_state.search_query, placeholder="キーワード検索...", label_visibility="collapsed")
    if b1_col.button("🔍 検索"): st.session_state.search_query = temp_q; st.rerun()
    if b2_col.button("クリア"): st.session_state.search_query = ""; st.rerun()

    df_list = get_data(SHEET_URL)
    if st.session_state.search_query:
        df_list = df_list[df_list['content'].str.contains(st.session_state.search_query, case=False, na=False) | df_list['date'].str.contains(st.session_state.search_query, na=False)]
    
    c_title.markdown(f"<p style='margin:0; padding-top:6px; font-weight:bold;'>📊 日記一覧（{len(df_list)}件）</p>", unsafe_allow_html=True)
    
    with st.container(height=520):
        for idx, row in df_list.iterrows():
            if st.button(f"📅 {row['date']}\n{row['content'][:50]}", key=f"l_{idx}"):
                st.session_state.edit_date = row['date']; st.session_state.edit_header = row['header']; st.session_state.current_page = "edit"; st.rerun()

# =====================================================================
# 3. 編集画面
# =====================================================================
elif st.session_state.current_page == "edit":
    if st.button("⬅️ 戻る"): st.session_state.current_page = "list"; st.rerun()
    df = get_data(SHEET_URL)
    val = df[df['date'] == st.session_state.edit_date]['content'].values[0] if not df[df['date'] == st.session_state.edit_date].empty else ""
    new_c = st.text_area("内容", value=val, height=300)
    if st.button("💾 保存", type="primary"): 
        if save_diary(st.session_state.edit_date, st.session_state.edit_header, new_c): st.success("保存完了"); st.session_state.current_page = "list"; st.rerun()
