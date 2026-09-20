@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  GDEA - Compilar ejecutable standalone
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Entorno no configurado. Ejecute setup.bat primero.
    pause
    exit /b 1
)

:: Instalar PyInstaller si no esta
.venv\Scripts\python.exe -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo Instalando PyInstaller...
    .venv\Scripts\python.exe -m pip install pyinstaller --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo instalar PyInstaller.
        pause
        exit /b 1
    )
)

:: Limpiar compilaciones anteriores
if exist "dist\GDEA" rmdir /s /q "dist\GDEA"
if exist "build\GDEA" rmdir /s /q "build\GDEA"

echo Compilando (puede tardar 3-5 minutos)...
echo.

:: python -m PyInstaller: el launcher pyinstaller.exe falla en silencio
:: en este entorno (Python 3.14 / scripts del venv).
.venv\Scripts\python.exe -m PyInstaller GDEA.spec --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo la compilacion. Revise los mensajes anteriores.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Compilacion exitosa.
echo.
echo  Ejecutable en: dist\GDEA\GDEA.exe
echo.
echo  Para distribuir a otro equipo:
echo    - Copie la carpeta  dist\GDEA\  completa al USB
echo    - En destino: ejecute GDEA.exe directamente
echo    - No requiere Python instalado
echo    - La primera vez crea gdea_config.json automaticamente
echo ============================================
pause
