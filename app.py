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
def initialize_state():
    defaults = {
        'current_page': "calendar",
        'selected_date': datetime.date.today(),
        'view_year': datetime.date.today().year,
        'view_month': datetime.date.today().month,
        'previous_date': None,
        'local_updates': {},
        'edit_date': "",
        'edit_header': "",
        'search_query': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_state()

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

# --- アプリ共通レイアウト用CSSスタイル定義（ボタン以外） ---
st.markdown("""
<style>
.main .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
.responsive-title { font-size: 1.6rem !important; font-weight: bold; text-align: center; margin-bottom: 8px !important; }
div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; width: 100% !important; gap: 2px !important; }
div[data-testid="stColumn"], div[data-testid="column"] { width: 0 !important; flex-grow: 1 !important; flex-shrink: 1 !important; flex-basis: 0% !important; min-width: 0 !important; padding: 0 !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# 画面１：カレンダー画面（メイン）
# =====================================================================
if st.session_state.current_page == "calendar":
    st.markdown("""
    <style>
    .stButton > button { width: 100% !important; padding: 0.4rem 0 !important; font-size: 0.75rem !important; margin: 0 !important; }
    .weekday-header { text-align: center; font-size: 0.75rem; font-weight: bold; color: #888888; margin: 0 0 3px 0; }
    div[data-testid="stSelectbox"] label { display: none !important; }
    div[data-testid="stSelectbox"] > div { margin: 0 !important; padding: 0 !important; }
    div[data-testid="stTextArea"] label { display: none !important; margin: 0 !important; padding: 0 !important; }
    div[data-testid="stTextArea"] { margin-top: 4px !important; }
    div[data-testid="stTextArea"] > div { position: relative !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)

    col_prev_year, col_year_select, col_next_year = st.columns([1, 2, 1])
    if col_prev_year.button("⏪ 前年", use_container_width=True):
        save_current_diary_if_changed()
        st.session_state.view_year -= 1
        st.rerun()

    year_options = list(range(st.session_state.view_year - 10, st.session_state.view_year + 11))
    selected_year = col_year_select.selectbox("年選択", options=year_options, index=year_options.index(st.session_state.view_year), label_visibility="collapsed")
    if selected_year != st.session_state.view_year:
        save_current_diary_if_changed()
        st.session_state.view_year = selected_year
        st.rerun()

    if col_next_year.button("翌年 ⏩", use_container_width=True):
        save_current_diary_if_changed()
        st.session_state.view_year += 1
        st.rerun()

    st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)

    col_prev_month, col_today, col_next_month = st.columns(3)
    if col_prev_month.button("◀ 前月", use_container_width=True):
        save_current_diary_if_changed()
        if st.session_state.view_month == 1:
            st.session_state.view_month = 12
            st.session_state.view_year -= 1
        else:
            st.session_state.view_month -= 1
        st.rerun()

    if col_today.button("Today", use_container_width=True):
        save_current_diary_if_changed()
        today = datetime.date.today()
        st.session_state.selected_date = today
        st.session_state.view_year = today.year
        st.session_state.view_month = today.month
        st.rerun()

    if col_next_month.button("翌月 ▶", use_container_width=True):
        save_current_diary_if_changed()
        if st.session_state.view_month == 12:
            st.session_state.view_month = 1
            st.session_state.view_year += 1
        else:
            st.session_state.view_month += 1
        st.rerun()

    st.markdown(f"<h4 style='text-align: center; margin: 8px 0; font-size: 1rem;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h4>", unsafe_allow_html=True)

    weekdays_headers = ["月", "火", "水", "木", "金", "土", "日"]
    cols_header = st.columns(7)
    for i, w in enumerate(weekdays_headers):
        cols_header[i].markdown(f"<p class='weekday-header'>{w}</p>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
    for week in cal:
        cols_days = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols_days[i].write("")
            else:
                current_loop_date_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
                is_selected = (st.session_state.selected_date.year == st.session_state.view_year and st.session_state.selected_date.month == st.session_state.view_month and st.session_state.selected_date.day == day)
                btn_type = "primary" if is_selected else "secondary"
                has_diary = current_loop_date_str in existing_dates or (current_loop_date_str in st.session_state.local_updates and st.session_state.local_updates[current_loop_date_str].strip() != "")
                button_label = f"🔹{day}" if has_diary else str(day)
                
                if cols_days[i].button(button_label, key=f"btn_{st.session_state.view_year}_{st.session_state.view_month}_{day}", type=btn_type, use_container_width=True):
                    save_current_diary_if_changed()
                    st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                    st.rerun()

    selected_date = st.session_state.selected_date
    date_str = selected_date.strftime("%Y-%m-%d")
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    header_str = f"{selected_date.year}年{selected_date.month}月{selected_date.day}日（{weekdays[selected_date.weekday()]}）"

    st.markdown(f"<p style='font-size: 0.95rem; font-weight: bold; margin: 8px 0 4px 0;'>{header_str}</p>", unsafe_allow_html=True)

    content_key = f"diary_content_{date_str}"
    if st.session_state.previous_date != date_str or content_key not in st.session_state:
        st.cache_data.clear()
        df = get_data(SHEET_URL)
        if date_str in st.session_state.local_updates:
            st.session_state[content_key] = st.session_state.local_updates[date_str]
        else:
            entry = df[df['date'] == date_str]
            val = entry['content'].values[0] if not entry.empty else ""
            st.session_state[content_key] = val
            if date_str not in st.session_state.local_updates:
                st.session_state.local_updates[date_str] = val
        st.session_state.previous_date = date_str

    content = st.text_area("", key=content_key, height=180)

    col_save, col_sync, col_list = st.columns([3, 1, 1])
    if col_save.button("保存", type="primary", use_container_width=True):
        if save_diary(date_str, header_str, content):
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

    if col_list.button("📊 一覧", use_container_width=True):
        save_current_diary_if_changed()
        st.session_state.current_page = "list"
        st.rerun()


# =====================================================================
# 画面２：一覧画面
# =====================================================================
elif st.session_state.current_page == "list":
    
    st.markdown("""
    <style>
    .stButton > button {
        height: auto !important;
        min-height: 4.5rem;
        padding: 0.6rem 0.8rem !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: flex-start !important;
        text-align: left !important;
        width: 1
