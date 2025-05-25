# ======== 解決繪圖中文字與 tkinter crash 問題 ========
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ======== 其他必要匯入 ========
import os
import yfinance as yf
import pandas as pd
from datetime import datetime

# ======== 設定輸出資料夾與錯誤日誌 ========
try:
    BASE_DIR = os.path.dirname(__file__)
except NameError:
    BASE_DIR = os.getcwd()
RESULTS_DIR = os.path.join(BASE_DIR, f"results_{datetime.today().strftime('%Y%m%d')}")
os.makedirs(RESULTS_DIR, exist_ok=True)
ERROR_LOG_PATH = os.path.join(RESULTS_DIR, "error_log.txt")

# ======== 股票清單 ========
tickers = ['2330.TW', '2317.TW', '2454.TW']

# ======== 策略參數 ========
short_window = 20
long_window = 60
summary_list = []
today = datetime.today().strftime('%Y-%m-%d')

# ======== 清空錯誤日誌 ========
with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
    f.write("")

# ======== 逐檔回測 ========
for ticker in tickers:
    print(f"正在處理：{ticker}...")

    success = False
    for suffix in ["", ".TWO"]:
        final_ticker = ticker if suffix == "" else ticker.replace(".TW", suffix)
        for attempt in range(3):
            try:
                data = yf.download(final_ticker, start="2015-04-01", end=today, progress=False)

                # 展開欄位（處理 MultiIndex）
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                # 確認資料有效
                if 'Close' in data.columns and not data.empty:
                    success = True
                    print(f"{final_ticker} 資料取得成功（第 {attempt+1} 次嘗試）")
                    break
            except Exception as e:
                pass
        if success:
            break

    if not success:
        print(f"{ticker} 抓取失敗，寫入錯誤日誌。")
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{ticker} 資料抓取失敗，無法回測。\n")
        continue

    # 清理與補資料
    data.index = pd.to_datetime(data.index, errors='coerce')
    data = data.dropna(subset=["Close"])

    # ======== 計算 SMA ========
    data['SMA20'] = data['Close'].rolling(window=short_window).mean()
    data['SMA60'] = data['Close'].rolling(window=long_window).mean()

    # ======== 建立訊號 ========
    data['Signal'] = 0
    data.loc[data['SMA20'] > data['SMA60'], 'Signal'] = 1
    data.loc[data['SMA20'] < data['SMA60'], 'Signal'] = -1
    data['Position'] = data['Signal'].shift(1)

    # ======== 計算報酬 ========
    data['Market Return'] = data['Close'].pct_change()
    data['Strategy Return'] = data['Position'] * data['Market Return']
    strategy_return = (1 + data['Strategy Return'].fillna(0)).prod() - 1
    buyhold_return = (1 + data['Market Return'].fillna(0)).prod() - 1

    # ======== 儲存 CSV ========
    results_df = data[['Close', 'SMA20', 'SMA60', 'Signal', 'Position', 'Strategy Return']].copy()
    results_df.reset_index(inplace=True)
    csv_path = os.path.join(RESULTS_DIR, f"{ticker}_trades.csv")
    results_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print("已儲存交易紀錄：", csv_path)

    # ======== 淨值圖表 ========
    data['Equity Curve'] = (1 + data['Strategy Return'].fillna(0)).cumprod()
    equity_curve = data[['Equity Curve']].copy().reset_index()
    equity_curve.columns = ['date', 'equity']
    curve_df = equity_curve.set_index('date')

    plt.figure(figsize=(8, 4))
    plt.plot(curve_df['equity'], label='策略淨值')
    plt.title(f'{ticker} SMA 策略 淨值曲線')
    plt.xlabel('日期')
    plt.ylabel('策略淨值')
    plt.legend()
    plt.tight_layout()
    curve_path = os.path.join(RESULTS_DIR, f"{ticker}_equity_curve.png")
    plt.savefig(curve_path, dpi=200)
    plt.close()
    print("已儲存淨值曲線圖：", curve_path)

    # ======== 整理報酬率摘要 ========
    summary_list.append({
        "Ticker": ticker,
        "Strategy Return": strategy_return * 100,
        "Buy & Hold Return": buyhold_return * 100
    })

# ======== 繪製總體績效圖表 ========
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
    plt.title('各股票報酬率比較 (2015~今日)')
    plt.xticks([i + bar_width / 2 for i in index], summary_df.index)
    plt.legend()
    plt.tight_layout()
    summary_chart_path = os.path.join(RESULTS_DIR, "summary_bar_chart.png")
    plt.savefig(summary_chart_path, dpi=200)
    plt.close()
    print(f"✅ 已儲存報酬率統計圖：{summary_chart_path}")
else:
    print("⚠️ 無任何可用的回測結果。請查看錯誤日誌：", ERROR_LOG_PATH)