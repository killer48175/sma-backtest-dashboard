import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image

# 自動建立資料夾避免錯誤
os.makedirs("results", exist_ok=True)

st.set_page_config(layout="wide")
st.title("📈 多股票 SMA 策略回測報表 Dashboard")

# ======== Summary 報酬率圖 ========
summary_path = "results/summary_bar_chart.png"
if os.path.exists(summary_path):
    st.subheader("報酬率總覽")
    st.image(summary_path, use_container_width=True)
else:
    st.warning("尚未產生 summary_bar_chart.png，請先執行回測程式")

# ======== 掃描所有檔案 ========
all_files = os.listdir("results")
tickers = sorted(set(f.split("_")[0] for f in all_files if f.endswith("_trades.csv")))

if not tickers:
    st.info("⚠️ 尚未有任何回測結果。請先執行回測程式產生 results/ 資料。")

for ticker in tickers:
    st.markdown(f"---\n### 📊 {ticker} 分析結果")

    # Equity Curve 圖片
    equity_path = f"results/{ticker}_equity_curve.png"
    if os.path.exists(equity_path):
        st.image(equity_path, caption=f"{ticker} 淨值曲線圖", use_container_width=True)
    else:
        st.warning(f"找不到 {ticker} 的 equity 曲線圖")

    # 交易紀錄 CSV
    csv_path = f"results/{ticker}_trades.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.dataframe(df, use_container_width=True)

        # 檔案下載
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ 下載交易紀錄 CSV",
            data=csv_bytes,
            file_name=f"{ticker}_trades.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"找不到 {ticker} 的交易紀錄檔案")