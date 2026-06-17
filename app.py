import streamlit as st
import requests
import datetime

# ==========================================
# 【必須】ここをご自身のGASウェブアプリURLに書き換えてください
# 最後に /exec がついているURLです。
GAS_URL = "https://script.google.com/macros/s/AKfycbxJyrIIwoXqd5MOHDRIRpnzbNGRNDiFwdJDqy2W40DDvELRo90c4YZndqj1EJ1BqjwL4w/exec"
# ==========================================

st.set_page_config(
    page_title="Momentum Diary",
    page_icon="📔",
    layout="centered"
)

# --- 内部関数: 日付形式の統一（Python側） ---
def normalize_date_obj(date_raw):
    """
    GASから送られてくる様々な日付表記をPythonのdateオブジェクトに統一する。
    重複排除のためのキーとして使用。
    """
    if not date_raw or date_raw == "":
        return None
        
    date_str = str(date_raw).strip().split(' ')[0] # 時間部分があれば捨てる
    
    # よくある形式をパース試行
    formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']
    
    # 曜日部分などを簡易的に除去（例: 2024-06-22（土） -> 2024-06-22）
    date_str = date_str.split('（')[0].split('(')[0]

    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
            
    # どうしてもパースできない場合
    return None

# --- データ取得・整形関数 ---
@st.cache_data(ttl=5) # キャッシュ時間は短めに設定
def get_processed_data():
    """
    GASから全データを取得し、Python側で以下の処理を行う：
    1. 日付の規格化
    2. 重複排除（同じ日付なら後勝ち）
    3. 並び替え（最新が上）
    """
    try:
        response = requests.get(GAS_URL, timeout=10)
        raw_data = response.json()
        
        # エラーが返ってきた場合
        if isinstance(raw_data, dict) and 'error' in raw_data:
            st.error(f"GAS側エラー: {raw_data['error']}")
            return {}

        # データの整形と重複排除 (Key: date_object, Value: content)
        unique_data_map = {}
        
        if isinstance(raw_data, list):
            for item in raw_data:
                # 日付をPythonのdate型に統一
                date_obj = normalize_date_obj(item.get('date'))
                
                if date_obj:
                    # Mapに入れることで、スプレッドシート下部にある（新しい）データが上書き採用される
                    unique_data_map[date_obj] = item.get('content', '')
        
        return unique_data_map

    except requests.exceptions.RequestException as e:
        st.error(f"通信エラー: {e}")
        return {}
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")
        return {}

# --- 自動保存用コールバック関数 ---
def auto_save():
    """
    テキストエリアの内容が変更されたら呼ばれる。
    指定した日付の行をGAS経由で上書き・追加する（軽量処理）。
    """
    # 現在選択されている日付を取得
    selected_date = st.session_state.get('diary_date_input', datetime.date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # ヘッダー文字列を作成（曜日はPython側で計算）
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    weekday_str = weekdays[selected_date.weekday()]
    header_str = f"{selected_date.year}年{selected_date.month}月{selected_date.day}日 ({weekday_str})"
    
    # 入力内容
    content = st.session_state.text_input

    # GASへのペイロード
    payload = {
        "date": date_str,
        "header": header_str,
        "content": content
    }

    try:
        # 保存リクエスト（timeoutを短くしてハングアップを防ぐ）
        requests.post(GAS_URL, json=payload, timeout=5)
        # 保存に成功したらキャッシュをクリアして、リロード時に最新が表示されるようにする
        st.cache_data.clear()
    except:
        # 保存失敗時はサイレントにスルー（ユーザー入力を阻害しないため）
        pass

# ==========================================
# メインUI構築
# ==========================================
st.title("📔 Momentum Diary")

# データ取得
processed_data_map = get_processed_data()

# サイドバー：日付選択
st.sidebar.header("メニュー")

# 初期日付の設定（session_stateを使用）
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# 日付選択カレンダー
selected_date = st.sidebar.date_input(
    "日付を選択",
    value=st.session_state.selected_date,
    key="diary_date_input"
)

# Todayボタン
if st.sidebar.button("今日"):
    st.session_state.selected_date = datetime.date.today()
    st.rerun()

# 選択された日付のデータを取得
current_content = processed_data_map.get(selected_date, "")

# 選択された日付の表示
date_str_display = selected_date.strftime("%Y年%m月%d日")
st.subheader(f"{date_str_display} の日記")

# 日記入力エリア（on_changeで自動保存）
st.text_area(
    "本文",
    value=current_content,
    height=450,
    key="text_input",
    on_change=auto_save,
    placeholder="ここに入力すると自動的に保存されます...",
    help="入力枠からフォーカスを外す（枠外をクリックする）と保存が走ります。"
)

st.caption(f"全データ件数（重複排除後）: {len(processed_data_map)} 件")
