@echo off
title TUTOIA - Plataforma de Sustentacion Inteligente
echo =======================================================
echo           INICIANDO TUTOIA (UTS 2026)
echo =======================================================
cd /d "%~dp0backend"

echo Verificando puerto 8000...
netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo [AVISO] El puerto 8000 parece estar ocupado por otra aplicacion.
    echo Iniciando servidor en el puerto 8001: http://localhost:8001
    start http://localhost:8001
    ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
) else (
    echo Iniciando servidor en el puerto 8000: http://localhost:8000
    start http://localhost:8000
    ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
)
pause
