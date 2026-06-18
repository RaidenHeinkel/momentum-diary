import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# --- 設定 ---
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lXoSqz_TNSuzKpnNOrytNJ5P6uc-Wjr3Q2Bp1-A0Fxk/gviz/tq?tqx=out:csv"
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

# --- スタイル定義 ---
CSS = """
<style>
.main .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
.responsive-title { font-size: 1.6rem !important; font-weight: bold; text-align: center; margin-bottom: 8px !important; }
.weekday-header { text-align: center; font-size: 0.75rem; font-weight: bold; color: #888888; margin: 0 0 3px 0; }
.stButton > button { width: 100% !important; padding: 0.4rem 0 !important; font-size: 0.75rem !important; }
div[data-testid="stSelectbox"] label { display: none !important; }
div[data-testid="stTextArea"] label { display: none !important; margin: 0 !important; }
</style>
"""

# --- 共通ユーティリティ ---
def get_data(url):
    return pd.read_csv(url).fillna("")

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

def get_formatted_header(d_obj):
    return f"{d_obj.year}年{d_obj.month}月{d_obj.day}日（{WEEKDAYS[d_obj.weekday()]}）"

def initialize_state():
    defaults = {
        'current_page': "calendar",
        'selected_date': datetime.date.today(),
        'view_year': datetime.date.today().year,
        'view_month': datetime.date.today().month,
        'previous_date': None,
        'local_updates': {},
        'edit_date': "",
        'edit_header': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_current_diary_if_changed():
    """画面遷移時に変更があれば保存する"""
    if st.session_state.previous_date:
        prev_key = f"diary_content_{st.session_state.previous_date}"
        if prev_key in st.session_state:
            current_input = st.session_state[prev_key]
            if current_input != st.session_state.local_updates.get(st.session_state.previous_date, "__NOT_SET__"):
                p_date = datetime.datetime.strptime(st.session_state.previous_date, "%Y-%m-%d").date()
                save_diary(st.session_state.previous_date, get_formatted_header(p_date), current_input)

# --- 画面表示関数 ---
def render_calendar():
    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)
    
    # 年選択UI
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⏪ 前年"):
        save_current_diary_if_changed()
        st.session_state.view_year -= 1
        st.rerun()
    
    year_options = list(range(st.session_state.view_year - 10, st.session_state.view_year + 11))
    selected_year = c2.selectbox("年選択", options=year_options, index=year_options.index(st.session_state.view_year), label_visibility="collapsed")
    if selected_year != st.session_state.view_year:
        save_current_diary_if_changed()
        st.session_state.view_year = selected_year
        st.rerun()

    if c3.button("翌年 ⏩"):
        save_current_diary_if_changed()
        st.session_state.view_year += 1
        st.rerun()

    # 月選択UI
    m1, m2, m3 = st.columns(3)
    if m1.button("◀ 前月"):
        save_current_diary_if_changed()
        if st.session_state.view_month == 1:
            st.session_state.view_month = 12
            st.session_state.view_year -= 1
        else:
            st.session_state.view_month -= 1
        st.rerun()
    
    if m2.button("Today"):
        save_current_diary_if_changed()
        today = datetime.date.today()
        st.session_state.update(selected_date=today, view_year=today.year, view_month=today.month)
        st.rerun()
        
    if m3.button("翌月 ▶"):
        save_current_diary_if_changed()
        if st.session_state.view_month == 12:
            st.session_state.view_month = 1
            st.session_state.view_year += 1
        else:
            st.session_state.view_month += 1
        st.rerun()

    st.markdown(f"<h4 style='text-align: center;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h4>", unsafe_allow_html=True)
    
    # カレンダーグリッド
    df_all = get_data(SHEET_URL)
    existing_dates = set(df_all[df_all['content'].str.strip() != '']['date'].tolist())
    
    # ヘッダー
    cols_header = st.columns(7)
    for i, w in enumerate(WEEKDAYS):
        cols_header[i].markdown(f"<p class='weekday-header'>{w}</p>", unsafe_allow_html=True)
    
    # 日付ボタン
    for week in calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month):
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: continue
            
            d_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
            is_selected = (st.session_state.selected_date == datetime.date(st.session_state.view_year, st.session_state.view_month, day))
            has_diary = d_str in existing_dates or (d_str in st.session_state.local_updates and st.session_state.local_updates[d_str].strip() != "")
            
            if cols[i].button(f"🔹{day}" if has_diary else str(day), type="primary" if is_selected else "secondary"):
                save_current_diary_if_changed()
                st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                st.rerun()

    # 日記入力エリア
    selected = st.session_state.selected_date
    date_str = selected.strftime("%Y-%m-%d")
    st.markdown(f"**{get_formatted_header(selected)}**")
    
    content_key = f"diary_content_{date_str}"
    if st.session_state.previous_date != date_str or content_key not in st.session_state:
        st.cache_data.clear()
        df = get_data(SHEET_URL)
        val = st.session_state.local_updates.get(date_str) or (df[df['date'] == date_str]['content'].values[0] if not df[df['date'] == date_str].empty else "")
        st.session_state[content_key] = val
        st.session_state.previous_date = date_str

    content = st.text_area("", key=content_key, height=180)
    
    c_save, c_sync, c_list = st.columns([3, 1, 1])
    if c_save.button("保存", type="primary"):
        if save_diary(date_str, get_formatted_header(selected), content): st.rerun()
        else: st.error("保存失敗")
    if c_sync.button("🔄 同期"):
        st.cache_data.clear()
        if content_key in st.session_state: del st.session_state[content_key]
        if date_str in st.session_state.local_updates: del st.session_state.local_updates[date_str]
        st.rerun()
    if c_list.button("📊 一覧"):
        save_current_diary_if_changed()
        st.session_state.current_page = "list"
        st.rerun()

def render_list():
    df = get_data(SHEET_URL)
    # ローカル更新の反映
    for d, c in st.session_state.local_updates.items():
        if d in df['date'].values: df.loc[df['date'] == d, 'content'] = c
        elif c.strip(): df = pd.concat([df, pd.DataFrame([{"date": d, "header": get_formatted_header(datetime.datetime.strptime(d, "%Y-%m-%d")), "content": c}])], ignore_index=True)
    
    df = df[df['content'].str.strip() != ''].sort_values(by='date', ascending=False)
    
    if st.button("⬅️ 戻る"):
        st.session_state.current_page = "calendar"
        st.rerun()
    
    query = st.text_input("", placeholder="🔍 検索...", label_visibility="collapsed")
    if query: df = df[df['content'].str.contains(query, case=False, na=False) | df['date'].str.contains(query, na=False)]
    
    st.subheader(f"日記一覧（{len(df)}件）")
    with st.container(height=520):
        for idx, row in df.iterrows():
            if st.button(f"📅 {row['date']}\n{row['content'][:100]}...", key=f"btn_{idx}"):
                st.session_state.update(edit_date=row['date'], edit_header=row['header'], current_page="edit")
                st.rerun()

def render_edit():
    if st.button("⬅️ 戻る"):
        st.session_state.current_page = "list"
        st.rerun()
    
    st.markdown(f"### {st.session_state.edit_header}")
    key = f"edit_content_{st.session_state.edit_date}"
    if key not in st.session_state:
        df = get_data(SHEET_URL)
        val = st.session_state.local_updates.get(st.session_state.edit_date) or (df[df['date'] == st.session_state.edit_date]['content'].values[0] if not df[df['date'] == st.session_state.edit_date].empty else "")
        st.session_state[key] = val
        
    content = st.text_area("", key=key, height=360)
    if st.button("💾 保存", type="primary"):
        if save_diary(st.session_state.edit_date, st.session_state.edit_header, content):
            st.success("保存完了")
        else: st.error("保存失敗")

# --- メイン処理 ---
st.set_page_config(page_title="Momentum Diary", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)
initialize_state()

if st.session_state.current_page == "calendar": render_calendar()
elif st.session_state.current_page == "list": render_list()
elif st.session_state.current_page == "edit": render_edit()
