@echo off
title SIH-2026
cd /d "%~dp0"

set SUPABASE_URL=https://nmbiilbiyxgfsfusnzht.supabase.co
set SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5tYmlpbGJpeXhnZnNmdXNuemh0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzIzMjAyNCwiZXhwIjoyMTAyODA4MDI0fQ.lxn4KDqFkvO6qqomCJ_vXjcyq85OhUeF_pxFXktnHEA

echo [SIH-2026] Starting server...
echo.
echo  Frontend : http://localhost:8000
echo  API docs : http://localhost:8000/docs
echo  Sentiment is triggered automatically on each comment submit.
echo.
echo  Press CTRL+C in this window to stop the server.
echo =========================================================
echo.

timeout /t 3 /nobreak >nul
start "" http://localhost:8000

python ml\preprocessing\api.py