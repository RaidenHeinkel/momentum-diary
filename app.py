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
        'search_query': "",
        'trigger_clear_search': False # 検索リセット用フラグ
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_state()

# --- 共通の保存関数 ---
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

# --- 共通CSS ---
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
    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)
    
    col_prev_year, col_year_select, col_next_year = st.columns([1, 2, 1])
    if col_prev_year.button("⏪ 前年", use_container_width=True):
        save_current_diary_if_changed()
        st.session_state.view_year -= 1
        st.rerun()

    year_options = list(range(st.session_state.view_year - 10, st.session_state.view_year + 11))
    selected_year = col_year_select.selectbox("年", options=year_options, index=year_options.index(st.session_state.view_year), label_visibility="collapsed")
    if selected_year != st.session_state.view_year:
        save_current_diary_if_changed()
        st.session_state.view_year = selected_year
        st.rerun()

    if col_next_year.button("翌年 ⏩", use_container_width=True):
        save_current_diary_if_changed()
        st.session_state.view_year += 1
        st.rerun()

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
    
    # カレンダー表示
    cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
    for week in cal:
        cols_days = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                d_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
                is_sel = (st.session_state.selected_date.year == st.session_state.view_year and st.session_state.selected_date.month == st.session_state.view_month and st.session_state.selected_date.day == day)
                if cols_days[i].button(str(day), type="primary" if is_sel else "secondary", use_container_width=True):
                    save_current_diary_if_changed()
                    st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                    st.rerun()

    # 日記入力
    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
    content_key = f"diary_content_{date_str}"
    
    if st.session_state.previous_date != date_str or content_key not in st.session_state:
        df = get_data(SHEET_URL)
        val = df[df['date'] == date_str]['content'].values[0] if not df[df['date'] == date_str].empty else ""
        st.session_state[content_key] = st.session_state.local_updates.get(date_str, val)
        st.session_state.previous_date = date_str

    content = st.text_area("", key=content_key, height=150)
    col1, col2, col3 = st.columns(3)
    if col1.button("保存", type="primary", use_container_width=True):
        save_diary(date_str, "", content)
        st.rerun()
    if col3.button("一覧", use_container_width=True):
        save_current_diary_if_changed()
        st.session_state.current_page = "list"
        st.rerun()


# =====================================================================
# 画面２：一覧画面
# =====================================================================
elif st.session_state.current_page == "list":
    # 検索窓クリア処理（ウィジェット生成前に実行）
    if st.session_state.get("trigger_clear_search"):
        if "diary_search_input" in st.session_state:
            del st.session_state["diary_search_input"]
        st.session_state.search_query = ""
        st.session_state.trigger_clear_search = False

    col_back, col_title = st.columns([1.5, 4.5])
    if col_back.button("⬅️ 戻る", use_container_width=True):
        # 戻る時は検索をクリアしてカレンダーへ
        if "diary_search_input" in st.session_state:
            del st.session_state["diary_search_input"]
        st.session_state.search_query = ""
        st.session_state.current_page = "calendar"
        st.rerun()

    col_search, col_clear = st.columns([4, 1.5])
    if col_clear.button("クリア", use_container_width=True):
        st.session_state.trigger_clear_search = True
        st.rerun()

    # 検索窓
    search_query = col_search.text_input("", placeholder="検索...", key="diary_search_input", label_visibility="collapsed")
    st.session_state.search_query = search_query

    # リスト生成
    df_list = get_data(SHEET_URL)
    # (省略: 以前と同様のデータ集計ロジック)
    df_list = df_list[df_list['content'].str.strip() != '']
    
    if search_query:
        df_list = df_list[df_list['content'].str.contains(search_query, case=False, na=False)]

    with st.container(height=500):
        for idx, row in df_list.iterrows():
            if st.button(f"{row['date']}: {row['content'][:20]}...", key=f"btn_{idx}", use_container_width=True):
                st.session_state.edit_date = row['date']
                st.session_state.edit_header = row['header']
                st.session_state.current_page = "edit"
                st.rerun()


# =====================================================================
# 画面３：編集画面
# =====================================================================
elif st.session_state.current_page == "edit":
    if st.button("⬅️ 一覧へ戻る"):
        st.session_state.current_page = "list"
        st.rerun()
    
    edit_key = f"edit_content_{st.session_state.edit_date}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = st.session_state.local_updates.get(st.session_state.edit_date, "")
    
    updated_text = st.text_area("内容", key=edit_key)
    if st.button("保存"):
        save_diary(st.session_state.edit_date, st.session_state.edit_header, updated_text)
        st.success("保存完了")
