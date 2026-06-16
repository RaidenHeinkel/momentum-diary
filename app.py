import streamlit as st
import requests
import pandas as pd

# 1. 手順2で発行したURLをここに貼り付けてください
GAS_URL = "https://script.google.com/macros/s/AKfycbyJtg-SZVpFnUUMxkJ1PkEUqHVOrBAjWhoK7xGQQFgEsniRMLMf6YDI5H2x2ORhZL1rYA/exec"

st.title("Momentum Diary")

# 2. スプレッドシートからデータを取得する（GASを経由してシート全体を読み込む）
# ※シートを公開設定にする必要があります（後述）
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT6UXrWkViMBqVFvkayaXQ76oKeh47-hDe9rbqOEFMAlppFcu-KDrz-MMsPUKFIGcHmjrkT8MmrT7SX/pub?output=csv"
csv_export_url = SHEET_URL.replace("/edit#gid=", "/export?format=csv&gid=")

@st.cache_data(ttl=5) # 5秒ごとに最新に更新
def get_data():
    return pd.read_csv(csv_export_url)

df = get_data()

# 3. 日付選択とデータの表示
selected_date = st.date_input("日付を選択")
date_str = selected_date.strftime("%Y-%m-%d")

# 該当するデータを探す
entry = df[df['date'] == date_str]
initial_text = entry['content'].values[0] if not entry.empty else ""

# 4. 入力エリア
content = st.text_area("日記の内容", value=initial_text, height=300)

# 5. 保存ボタン
if st.button("保存"):
    payload = {"date": date_str, "header": date_str, "content": content}
    response = requests.post(GAS_URL, json=payload)
    if response.status_code == 200:
        st.success("保存しました！")
        st.rerun() # リロードして最新状態にする
    else:
        st.error("保存に失敗しました")