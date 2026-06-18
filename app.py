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

# =====================================================================
# 画面１：カレンダー
# =====================================================================
if st.session_state.current_page == "calendar":
    st.title("Momentum Diary")

    # 年・月操作
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

    st.subheader(f"{st.session_state.view_year}年 {st.session_state.view_month}月")
    
    # カレンダー描画
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

    sel_d = st.session_state.selected_date
    d_str = sel_d.strftime("%Y-%m-%d")
    st.write(f"日付: {d_str}")

    content_key = f"c_{d_str}"
    if st.session_state.previous_date != d_str or content_key not in st.session_state:
        if d_str in st.session_state.local_updates:
            st.session_state[content_key] = st.session_state.local_updates[d_str]
        else:
            entry = df_all[df_all['date'] == d_str]
            st.session_state[content_key] = entry['content'].values[0] if not entry.empty else ""
        st.session_state.previous_date = d_str

    content = st.text_area("日記内容", key=content_key)
    
    if st.button("保存"):
        if save_diary(d_str, f"{sel_d.year}年{sel_d.month}月{sel_d.day}日", content): st.rerun()
    if st.button("📊 一覧へ"): st.session_state.current_page = "list"; st.rerun()

# =====================================================================
# 画面２：一覧（不備データ完全無視・頑丈版）
# =====================================================================
elif st.session_state.current_page == "list":
    st.title("日記一覧")
    if st.button("⬅️ 戻る"): st.session_state.current_page = "calendar"; st.rerun()

    df_src = get_data(SHEET_URL)
    
    # データをクリーニングして不正な行を無視する処理
    valid_rows = []
    for idx, row in df_src.iterrows():
        content_val = str(row['content']).strip()
        if content_val == "": continue
        try:
            date_val = str(row['date']).strip()
            # 日付の形式チェック
            pd_d = datetime.datetime.strptime(date_val, "%Y-%m-%d").date()
            valid_rows.append({"date": date_val, "content": content_val, "parsed_date": pd_d})
        except:
            continue # 日付が不正な行は無視する

    if valid_rows:
        df_list = pd.DataFrame(valid_rows).sort_values(by='parsed_date', ascending=False)
        for idx, row in df_list.iterrows():
            if st.button(f"{row['date']}: {row['content'][:30]}..."):
                st.session_state.edit_date = row['date']
                st.session_state.current_page = "edit"; st.rerun()
    else:
        st.write("データがありません")

# =====================================================================
# 画面３：編集
# =====================================================================
elif st.session_state.current_page == "edit":
    st.title("編集")
    ed = st.session_state.edit_date
    if st.button("戻る"): st.session_state.current_page = "list"; st.rerun()
    
    st.write(f"日付: {ed}")
    ek = f"e_{ed}"
    if ek not in st.session_state:
        df_e = get_data(SHEET_URL)
        entry = df_e[df_e['date'] == ed]
        st.session_state[ek] = entry['content'].values[0] if not entry.empty else ""
        
    up_c = st.text_area("内容", key=ek)
    if st.button("保存して戻る"):
        if save_diary(ed, ed, up_c): st.session_state.current_page = "list"; st.rerun()
