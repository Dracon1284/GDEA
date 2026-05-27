@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Entorno no configurado. Ejecutando setup...
    call setup.bat
)

.venv\Scripts\python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] El programa termino con errores.
    pause
)
