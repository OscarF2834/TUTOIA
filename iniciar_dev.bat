@echo off
setlocal
title TUTOIA - Entorno de DESARROLLO (UTS 2026)

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"
set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"

echo =======================================================
echo        TUTOIA - MODO DESARROLLO (UTS 2026)
echo =======================================================

if not exist "%PYTHON_EXE%" (
    echo [ERROR] No se encontro el entorno virtual en: "%PYTHON_EXE%"
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [ERROR] No se encontro node_modules en frontend. Ejecuta "npm install" primero.
    pause
    exit /b 1
)

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [ERROR] El puerto 8000 ya esta en uso.
    echo         El proxy de Vite en desarrollo requiere el backend en el puerto 8000.
    echo         Cierra el proceso que usa el puerto 8000 y vuelve a intentar.
    pause
    exit /b 1
)

netstat -ano | findstr ":5173 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [ERROR] El puerto 5173 ya esta en uso por otra instancia de Vite.
    pause
    exit /b 1
)

echo [1/2] Levantando Backend FastAPI (--reload) en http://127.0.0.1:8000 ...
start "TUTOIA - Backend (Dev :8000)" /D "%BACKEND_DIR%" cmd /k ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

echo [2/2] Levantando Frontend Vite (HMR) en http://localhost:5173 ...
start "TUTOIA - Frontend (Dev :5173)" /D "%FRONTEND_DIR%" cmd /k npm run dev

echo.
echo Abriendo navegador en http://localhost:5173 ...
echo Swagger API disponible en http://127.0.0.1:8000/docs
echo.
echo Para detener el entorno, cierra ambas ventanas o presiona CTRL+C en cada una.
timeout /t 3 /nobreak >nul
start http://localhost:5173
