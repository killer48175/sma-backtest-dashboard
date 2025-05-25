@echo off
cd /d %~dp0
echo Running 0050 SMA backtest...
"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe" "multi_stock_sma_strategy.py"
pause
