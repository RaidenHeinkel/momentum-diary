import streamlit as st
import requests
import pandas as pd
import datetime
import calendar

# 設定：GASのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbzuP38pZNYdVFX_i3_678YwOhm6MHffqB8vayoEqHvmiKHF8yVX3vEOkHInLqBSANsi/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lXoSqz_TNSuzKpnNOrytNJ5P6uc-Wjr3Q2Bp1-A0Fxk/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Momentum Diary", layout="centered")

# --- データ読み込み ---
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

# --- 💾 保存通信 ---
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

# データの先読み
df_all = get_data(SHEET_URL)
existing_dates = set(df_all[df_all['content'].str.strip() != '']['date'].tolist())

# --- ⚙️ 共通CSS ---
st.markdown("""
<style>
.main .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
.responsive-title { font-size: 1.6rem !important; font-weight: bold; text-align: center; margin-bottom: 8px !important; }
div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; width: 100% !important; gap: 4px !important; }
div[data-testid="stColumn"], div[data-testid="column"] { width: 0 !important; flex-grow: 1 !important; flex-shrink: 1 !important; flex-basis: 0% !important; min-width: 0 !important; padding: 0 !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 画面１：カレンダー
# =====================================================================
if st.session_state.current_page == "calendar":
    st.markdown("""
    <style>
    .stButton > button { width: 100% !important; padding: 0.4rem 0 !important; font-size: 0.75rem !important; margin: 0 !important; }
    .weekday-header { text-align: center; font-size: 0.75rem; font-weight: bold; color: #888888; margin: 0 0 3px 0; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("<h1 class='responsive-title'>Momentum Diary</h1>", unsafe_allow_html=True)

    # 年・月・Today操作
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⏪ 前年"): st.session_state.view_year -= 1; st.rerun()
    year_options = list(range(st.session_state.view_year - 10, st.session_state.view_year + 11))
    sy = c2.selectbox("", options=year_options, index=year_options.index(st.session_state.view_year), label_visibility="collapsed")
    if sy != st.session_state.view_year: st.session_state.view_year = sy; st.rerun()
    if c3.button("翌年 ⏩"): st.session_state.view_year += 1; st.rerun()

    c1, c2, c3 = st.columns(3)
    if c1.button("◀ 前月"):
        if st.session_state.view_month == 1: st.session_state.view_month = 12; st.session_state.view_year -= 1
        else: st.session_state.view_month -= 1
        st.rerun()
    if c2.button("Today"):
        t = datetime.date.today(); st.session_state.selected_date = t; st.session_state.view_year = t.year; st.session_state.view_month = t.month; st.rerun()
    if c3.button("翌月 ▶"):
        if st.session_state.view_month == 12: st.session_state.view_month = 1; st.session_state.view_year += 1
        else: st.session_state.view_month += 1
        st.rerun()

    st.markdown(f"<h4 style='text-align: center; margin: 8px 0;'>{st.session_state.view_year}年 {st.session_state.view_month}月</h4>", unsafe_allow_html=True)
    
    # カレンダー描画
    weekdays_headers = ["月", "火", "水", "木", "金", "土", "日"]
    cols_h = st.columns(7)
    for i, w in enumerate(weekdays_headers): cols_h[i].markdown(f"<p class='weekday-header'>{w}</p>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                d_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
                is_sel = (st.session_state.selected_date.day == day and st.session_state.selected_date.month == st.session_state.view_month and st.session_state.selected_date.year == st.session_state.view_year)
                has_d = d_str in existing_dates or (d_str in st.session_state.local_updates and st.session_state.local_updates[d_str].strip() != "")
                label = f"🔹{day}" if has_d else str(day)
                if cols[i].button(label, key=f"d_{d_str}", type="primary" if is_sel else "secondary"):
                    st.session_state.selected_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                    st.rerun()

    # 下部入力エリア
    sel_d = st.session_state.selected_date
    d_str = sel_d.strftime("%Y-%m-%d")
    header_str = f"{sel_d.year}年{sel_d.month}月{sel_d.day}日（{weekdays_headers[sel_d.weekday()]}）"
    st.markdown(f"<p style='font-weight: bold; margin: 8px 0;'>{header_str}</p>", unsafe_allow_html=True)

    content_key = f"c_{d_str}"
    if st.session_state.previous_date != d_str or content_key not in st.session_state:
        if d_str in st.session_state.local_updates:
            st.session_state[content_key] = st.session_state.local_updates[d_str]
        else:
            entry = df_all[df_all['date'] == d_str]
            st.session_state[content_key] = entry['content'].values[0] if not entry.empty else ""
        st.session_state.previous_date = d_str

    content = st.text_area("", key=content_key, height=180, label_visibility="collapsed")
    
    col_s, col_sy, col_l = st.columns([3, 1, 1])
    if col_s.button("保存", type="primary"):
        if save_diary(d_str, header_str, content): st.rerun()
    if col_sy.button("🔄"): st.cache_data.clear(); st.rerun()
    if col_l.button("📊 一覧"): st.session_state.current_page = "list"; st.rerun()

# =====================================================================
# 画面２：一覧（💡外部部品不要！標準検索ハック版）
# =====================================================================
elif st.session_state.current_page == "list":
    st.markdown("""
    <style>
    /* 全ボタンを左寄せ ＆ はみ出し防止 */
    .stButton > button { width: 100% !important; text-align: left !important; justify-content: flex-start !important; align-items: flex-start !important; display: flex !important; flex-direction: column !important; height: auto !important; min-height: 4.5rem; padding: 0.6rem 0.8rem !important; }
    .stButton > button * { text-align: left !important; justify-content: flex-start !important; width: 100% !important; display: block !important; white-space: pre-wrap !important; }
    .stButton > button p { -webkit-line-clamp: 5; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; font-size: 0.85rem !important; line-height: 1.4 !important; }
    
    /* ⬅️ 戻るボタン専用スタイル（横並び安定化） */
    div[data-testid="column"]:first-child .stButton > button { 
        display: inline-flex !important; flex-direction: row !important; justify-content: center !important; align-items: center !important; text-align: center !important; 
        min-height: auto !important; height: 34px !important; padding: 0 !important; font-size: 0.85rem !important; margin-top: 4px !important;
    }
    div[data-testid="column"]:first-child .stButton > button * { text-align: center !important; width: auto !important; display: inline-block !important; }
    
    /* 📱 スマホ用：タイトル1行固定化 */
    .list-title-text {
        margin: 0; padding-top: 8px; font-weight: bold; white-space: nowrap; text-align: right;
        font-size: calc(0.9rem + 0.4vw) !important;
    }
    /* 🔍 検索ボックス内のフォント微調整 */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] { font-size: 0.9rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # データ準備
    df_list = get_data(SHEET_URL)
    for d, c in st.session_state.local_updates.items():
        if d in df_list['date'].values: df_list.loc[df_list['date'] == d, 'content'] = c
        elif c.strip() != "":
            pd_d = datetime.datetime.strptime(d, "%Y-%m-%d").date()
            p_h = f"{pd_d.year}年{pd_d.month}月{pd_d.day}日（{["月","火","水","木","金","土","日"][pd_d.weekday()]}）"
            df_list = pd.concat([df_list, pd.DataFrame([{"date": d, "header": p_h, "content": c}])], ignore_index=True)
    df_list = df_list[df_list['content'].str.strip() != ''].sort_values(by='date', ascending=False).reset_index(drop=True)

    # ヘッダー
    cb, ct = st.columns([1.1, 4.9])
    if cb.button("⬅️ 戻る"): st.session_state.current_page = "calendar"; st.rerun()
    t_place = ct.empty()

    # 💡 標準セレクトボックスを「Enterキー不要のリアルタイム検索窓」にハック！
    # 入力枠に文字を打ち込むと、スマホのキーボード確定前でも候補がリアルタイムに絞り込まれます
    search_options = ["🔍 すべて表示"] + [f"{row['date']} : {row['content'][:40].replace('\n', ' ')}" for _, row in df_list.iterrows()]
    selected_search = st.selectbox("", options=search_options, index=0, label_visibility="collapsed")

    # 選択または入力内容に基づいて一覧を絞り込み
    if selected_search != "🔍 すべて表示":
        chosen_date = selected_search.split(" : ")[0]
        df_list = df_list[df_list['date'] == chosen_date]
    
    t_place.markdown(f"<p class='list-title-text'>📊 日記一覧（{len(df_list)}件）</p>", unsafe_allow_html=True)

    if df_list.empty: st.info("見つかりませんでした。")
    else:
        with st.container(height=520):
            for idx, row in df_list.iterrows():
                pd_d = datetime.datetime.strptime(row['date'], "%Y-%m-%d").date()
                w = ["月","火","水","木","金","土","日"][pd_d.weekday()]
                txt = f"📅 {row['date']}（{w}）\n{row['content']}"
                if st.button(txt, key=f"l_{idx}"):
                    st.session_state.edit_date = row['date']
                    st.session_state.edit_header = row['header']
                    st.session_state.current_page = "edit"; st.rerun()

# =====================================================================
# 画面３：編集
# =====================================================================
elif st.session_state.current_page == "edit":
    st.markdown("<style>.stButton > button { padding: 0.4rem !important; }</style>", unsafe_allow_html=True)
    ed, eh = st.session_state.edit_date, st.session_state.edit_header
    ek = f"e_{ed}"
    if ek not in st.session_state:
        if ed in st.session_state.local_updates: st.session_state[ek] = st.session_state.local_updates[ed]
        else:
            df_e = get_data(SHEET_URL)
            entry = df_e[df_e['date'] == ed]
            st.session_state[ek] = entry['content'].values[0] if not entry.empty else ""

    cb, ct = st.columns([1.3, 4.7])
    if cb.button("⬅️ 戻る"): st.session_state.current_page = "list"; st.rerun()
    ct.markdown("<p style='margin:0; padding-top:6px; font-size:1.1rem; font-weight:bold;'>📝 日記編集</p>", unsafe_allow_html=True)

    st.markdown(f"### {eh}")
    up_c = st.text_area("", key=ek, height=360, label_visibility="collapsed")
    if st.button("💾 保存", type="primary", use_container_width=True):
        if save_diary(ed, eh, up_c): st.success("保存完了！")
