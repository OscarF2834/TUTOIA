@echo off
setlocal
title TUTOIA - Entorno de PRODUCCION (UTS 2026)

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"
set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"

echo =======================================================
echo        TUTOIA - MODO PRODUCCION (UTS 2026)
echo =======================================================

if not exist "%PYTHON_EXE%" (
    echo [ERROR] No se encontro el entorno virtual en: "%PYTHON_EXE%"
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [INFO] Instalando dependencias del frontend...
    pushd "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        popd
        echo [ERROR] Fallo npm install.
        pause
        exit /b 1
    )
    popd
)

echo [1/3] Compilando frontend para produccion (dist)...
pushd "%FRONTEND_DIR%"
call npm run build
if errorlevel 1 (
    popd
    echo [ERROR] Fallo la compilacion del frontend.
    pause
    exit /b 1
)
popd

echo [2/3] Verificando puerto 8000...
set "PORT=8000"
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [AVISO] El puerto 8000 esta ocupado. Usando puerto 8001.
    set "PORT=8001"
)

echo [3/3] Iniciando servidor unico en http://localhost:%PORT%
echo       (Sirve API FastAPI + Frontend compilado)
echo       Presiona CTRL+C para detener el servidor.
echo.

cd /d "%BACKEND_DIR%"
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:%PORT%"
"%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%

pause
