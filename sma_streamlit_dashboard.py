import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="SMA 策略分析儀表板", layout="centered")
st.title("📈 SMA 策略回測工具 (2015~今日)")

st.sidebar.header("🔧 參數設定")
ticker_list = st.sidebar.text_input("輸入多個股票代碼（用逗號分隔，如 2330.TW,2317.TW）", value="2330.TW,2317.TW")
short_window = st.sidebar.slider("短期 SMA (SMA1)", 5, 60, 20)
long_window = st.sidebar.slider("長期 SMA (SMA2)", 30, 200, 60)
period_choice = st.sidebar.radio("回測資料區間", ["全期間 (2015~今日)", "最近一年"])
start_date = "2015-04-01" if period_choice == "全期間 (2015~今日)" else (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
strategy_option = st.sidebar.selectbox("策略類型", ["SMA 交叉策略", "黃金/死亡交叉", "動能策略"])
run_button = st.sidebar.button("開始回測")

if run_button:
    tickers = [t.strip() for t in ticker_list.split(',') if t.strip()]
    all_results = []
    equity_curves = pd.DataFrame()

    for ticker in tickers:
        st.subheader(f"📊 {ticker} 回測結果")
        with st.spinner(f"正在處理 {ticker}..."):
            try:
                today = datetime.today().strftime('%Y-%m-%d')
                data = yf.download(ticker, start=start_date, end=today)

                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                if 'Close' not in data.columns or data.empty:
                    st.error(f"{ticker} 無法取得有效資料。請檢查代碼是否正確。")
                    continue

                data['SMA1'] = data['Close'].rolling(window=short_window).mean()
                data['SMA2'] = data['Close'].rolling(window=long_window).mean()
                data['Signal'] = 0

                if strategy_option == "SMA 交叉策略":
                    data.loc[data['SMA1'] > data['SMA2'], 'Signal'] = 1
                    data.loc[data['SMA1'] < data['SMA2'], 'Signal'] = -1
                elif strategy_option == "黃金/死亡交叉":
                    cross_up = (data['SMA1'] > data['SMA2']) & (data['SMA1'].shift(1) <= data['SMA2'].shift(1))
                    cross_down = (data['SMA1'] < data['SMA2']) & (data['SMA1'].shift(1) >= data['SMA2'].shift(1))
                    data.loc[cross_up, 'Signal'] = 1
                    data.loc[cross_down, 'Signal'] = -1
                elif strategy_option == "動能策略":
                    data['Signal'] = data['Close'].pct_change(periods=short_window)
                    data['Signal'] = data['Signal'].apply(lambda x: 1 if x > 0 else -1)

                data['Position'] = data['Signal'].shift(1)
                data['Market Return'] = data['Close'].pct_change()
                data['Strategy Return'] = data['Position'] * data['Market Return']
                data['Equity Curve'] = (1 + data['Strategy Return'].fillna(0)).cumprod()

                strategy_return = (1 + data['Strategy Return'].fillna(0)).prod() - 1
                buyhold_return = (1 + data['Market Return'].fillna(0)).prod() - 1

                all_results.append({
                    "Ticker": ticker,
                    "SMA 策略報酬率": strategy_return * 100,
                    "買進持有報酬率": buyhold_return * 100
                })

                equity_curves[ticker] = data['Equity Curve']

                st.metric("SMA 策略報酬率", f"{strategy_return*100:.2f}%")
                st.metric("買進持有報酬率", f"{buyhold_return*100:.2f}%")

                fig, ax = plt.subplots(figsize=(10, 4))
                data['Equity Curve'].plot(ax=ax, label='策略淨值')
                buy_signals = data[(data['Signal'] == 1) & (data['Signal'].shift(1) != 1)]
                sell_signals = data[(data['Signal'] == -1) & (data['Signal'].shift(1) != -1)]
                ax.plot(buy_signals.index, data.loc[buy_signals.index, 'Equity Curve'], '^', markersize=8, color='green', label='買進')
                ax.plot(sell_signals.index, data.loc[sell_signals.index, 'Equity Curve'], 'v', markersize=8, color='red', label='賣出')
                ax.set_ylabel("策略淨值")
                ax.set_xlabel("日期")
                ax.legend()
                st.pyplot(fig)

                st.dataframe(data[['Close', 'SMA1', 'SMA2', 'Signal', 'Position']].dropna().tail(30))

            except Exception as e:
                st.error(f"{ticker} 發生錯誤：{e}")

    if all_results:
        st.subheader("📊 多股票報酬率比較總覽")
        results_df = pd.DataFrame(all_results)
        st.dataframe(results_df.set_index("Ticker"))

        st.subheader("📈 多股票策略淨值比較圖")
        fig, ax = plt.subplots(figsize=(10, 5))
        equity_curves.dropna().plot(ax=ax)
        ax.set_ylabel("策略淨值")
        ax.set_xlabel("日期")
        ax.set_title("多股票 SMA 策略淨值曲線")
        st.pyplot(fig)