@echo off
cd /d "%~dp0"

start "SIH-2026 API" /b python ml\preprocessing\api.py
timeout /t 2 /nobreak >nul
start "" http://localhost:8000