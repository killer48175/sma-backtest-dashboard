# Organized imports
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Streamlit page configuration
st.set_page_config(page_title="SMA Multi-Stock Backtest", layout="wide")
st.title("📈 SMA Multi-Stock Strategy Backtest Analysis")

# Sidebar settings
st.sidebar.header("🔧 Settings")
tickers_input = st.sidebar.text_input("Enter stock symbols (comma separated, e.g. 2330.TW,2317.TW)", value="2330.TW,2317.TW")
short_window = st.sidebar.slider("Short SMA (SMA1)", 5, 60, 20)
long_window = st.sidebar.slider("Long SMA (SMA2)", 30, 200, 60)
date_range = st.sidebar.radio("Backtest Period", ["All", "Last 1 Year"])
strategy_type = st.sidebar.selectbox("Strategy Type", ["SMA Crossover", "Golden/Death Cross", "Momentum"])

run = st.sidebar.button("Run Backtest")

# Helper function to fetch stock data
def fetch_data(ticker, start, end, retry=2):
    """Fetch stock data from Yahoo Finance."""
    for i in range(retry):
        try:
            data = yf.download(ticker, start=start, end=end, progress=False)
            return data
        except Exception:
            time.sleep(1)
    return pd.DataFrame()

# Main logic
if run:
    # Parse user inputs
    tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]
    today = datetime.today().strftime('%Y-%m-%d')
    start_date = "2015-04-01" if date_range == "All" else (datetime.today().replace(year=datetime.today().year - 1).strftime('%Y-%m-%d'))

    all_equity = pd.DataFrame()
    summary_list = []

    # Progress bar initialization
    progress = st.progress(0, text="Backtesting...")

    for idx, ticker in enumerate(tickers):
        st.subheader(f"📊 {ticker} Strategy Result")
        try:
            # Fetch and validate data
            data = fetch_data(ticker, start=start_date, end=today)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            if "Close" not in data.columns or data.empty or data["Close"].isnull().all():
                st.warning(f"{ticker} has no valid data")
                continue

            # Calculate SMA and signals
            data['SMA1'] = data['Close'].rolling(window=short_window).mean()
            data['SMA2'] = data['Close'].rolling(window=long_window).mean()

            data['Signal'] = 0
            if strategy_type == "SMA Crossover":
                data.loc[data['SMA1'] > data['SMA2'], 'Signal'] = 1
                data.loc[data['SMA1'] < data['SMA2'], 'Signal'] = -1
            elif strategy_type == "Golden/Death Cross":
                cond_buy = (data['SMA1'] > data['SMA2']) & (data['SMA1'].shift(1) <= data['SMA2'].shift(1))
                cond_sell = (data['SMA1'] < data['SMA2']) & (data['SMA1'].shift(1) >= data['SMA2'].shift(1))
                data.loc[cond_buy, 'Signal'] = 1
                data.loc[cond_sell, 'Signal'] = -1
            elif strategy_type == "Momentum":
                data['Momentum'] = data['Close'].pct_change(periods=10)
                data.loc[data['Momentum'] > 0, 'Signal'] = 1
                data.loc[data['Momentum'] < 0, 'Signal'] = -1

            # Calculate returns and equity curve
            data['Position'] = data['Signal'].shift(1)
            data['Market Return'] = data['Close'].pct_change()
            data['Strategy Return'] = data['Position'] * data['Market Return']
            data['Equity Curve'] = (1 + data['Strategy Return'].fillna(0)).cumprod()

            # Skip if not enough data
            if data[['SMA1', 'SMA2', 'Equity Curve']].dropna().empty:
                st.warning(f"{ticker} has insufficient data for strategy calculation")
                continue

            # Calculate performance metrics
            strategy_return = (1 + data['Strategy Return'].fillna(0)).prod() - 1
            buyhold_return = (1 + data['Market Return'].fillna(0)).prod() - 1

            summary_list.append({
                "Ticker": ticker,
                "SMA Strategy Return (%)": strategy_return * 100,
                "Buy & Hold Return (%)": buyhold_return * 100
            })

            # Plot equity curve
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(data['Equity Curve'], label='Strategy Equity')

            # Mark buy/sell points
            buy_signals = data[(data['Signal'] == 1) & (data['Signal'].shift(1) != 1)]
            sell_signals = data[(data['Signal'] == -1) & (data['Signal'].shift(1) != -1)]
            ax.plot(buy_signals.index, data.loc[buy_signals.index, 'Equity Curve'], '^', markersize=8, color='green', label='Buy')
            ax.plot(sell_signals.index, data.loc[sell_signals.index, 'Equity Curve'], 'v', markersize=8, color='red', label='Sell')

            ax.set_title(f"{ticker} Strategy Equity Curve")
            ax.legend()
            st.pyplot(fig)
            plt.close(fig)

            # Display data table
            st.dataframe(data[['Close', 'SMA1', 'SMA2', 'Signal', 'Position']].dropna().tail(20))

            # Save for merged equity curve
            all_equity[ticker] = data['Equity Curve']

        except Exception as e:
            st.error(f"{ticker} error: {e}")

        # Update progress bar
        progress.progress((idx + 1) / len(tickers), text=f"Completed {idx + 1}/{len(tickers)}")

    progress.empty()

    # Multi-stock merged equity curve
    if not all_equity.empty:
        all_equity = all_equity.dropna(axis=1, how='all')
        if not all_equity.empty:
            st.subheader("📈 Multi-Stock Strategy Equity Comparison")
            fig2, ax2 = plt.subplots(figsize=(12, 5))
            (all_equity / all_equity.iloc[0]).plot(ax=ax2)
            ax2.set_title("Normalized Strategy Equity Comparison")
            ax2.set_ylabel("Normalized Equity")
            st.pyplot(fig2)
            plt.close(fig2)

    # Show backtest summary table
    if summary_list:
        summary_df = pd.DataFrame(summary_list).set_index("Ticker")
        st.subheader("📋 Backtest Performance Summary")
        st.dataframe(summary_df.style.format("{:.2f}"))
        st.download_button("Download Performance Table (CSV)", summary_df.to_csv().encode("utf-8-sig"), file_name="sma_summary.csv", mime="text/csv")