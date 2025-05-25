import os
import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ======== 設定 results 資料夾路徑（與本程式同層） ========
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 這裡定義你的股票清單
tickers = ['2330.TW', '2317.TW', '2454.TW']

# ...你的股票清單、資料抓取與策略計算程式...

summary_list = []

for ticker in tickers:
    # ...你的回測邏輯，產生 results_df, equity_curve, strategy_return, buyhold_return...

    # 儲存交易紀錄
    csv_path = os.path.join(RESULTS_DIR, f"{ticker}_trades.csv")
    results_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print("已儲存交易紀錄:", csv_path)

    # 儲存淨值圖
    curve_df = pd.DataFrame(equity_curve).set_index('date')
    plt.figure(figsize=(8,4))
    plt.plot(curve_df['equity'], label='Equity Curve')
    plt.title(f'{ticker} SMA 策略 淨值曲線')
    plt.xlabel('Date')
    plt.ylabel('Equity')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f"{ticker}_equity_curve.png"), dpi=200)
    plt.close()
    print("已儲存淨值曲線圖")

    # 收集 summary
    summary_list.append({
        "Ticker": ticker,
        "Strategy Return": strategy_return,
        "Buy & Hold Return": buyhold_return
    })

# ======== 畫出總體報酬率柱狀圖 ========
if summary_list:
    summary_df = pd.DataFrame(summary_list)
    summary_df.set_index('Ticker', inplace=True)

    plt.figure(figsize=(10, 5))
    bar_width = 0.35
    index = range(len(summary_df))

    plt.bar(index, summary_df['Strategy Return'], bar_width, label='SMA 策略')
    plt.bar([i + bar_width for i in index], summary_df['Buy & Hold Return'], bar_width, label='買進持有')

    plt.xlabel('股票代碼')
    plt.ylabel('報酬率 (%)')
    plt.title('各股票報酬率比較 (2022~2024)')
    plt.xticks([i + bar_width / 2 for i in index], summary_df.index)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "summary_bar_chart.png"), dpi=200)
    plt.close()
    print(f"已儲存報酬率統計圖：{os.path.join(RESULTS_DIR, 'summary_bar_chart.png')}")