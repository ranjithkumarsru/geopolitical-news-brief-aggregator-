@echo off
title Geopolitical News Brief Aggregator
cd /d "%~dp0"
echo ===================================================
echo   Geopolitical News Brief Aggregator
echo   Starting local live dashboard...
echo ===================================================
echo.
python -m streamlit run app.py
pause
