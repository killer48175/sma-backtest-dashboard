# 0050 Constituents SMA Backtest Package

## Files
- `multi_stock_sma_strategy.py` : Python script for backtesting SMA strategy on Taiwan 0050 ETF constituents.
- `run_strategy.bat` : Windows batch file to execute the Python script using the specified Python interpreter.
- `results/` : Folder created at runtime, containing CSV and PNG outputs for each stock.

## Instructions
1. **Extract** this package into an **English-named** folder, e.g., `C:\Users\kille\strategy`.
2. Ensure you have installed the required Python packages:
   ```
   pip install requests beautifulsoup4 yfinance pandas matplotlib
   ```
3. **Double-click** `run_strategy.bat` to run the backtest.  
   This will produce:
   - `results/{ticker}_trades.csv`
   - `results/{ticker}_equity_curve.png`
4. Check the `results/` folder for outputs.
