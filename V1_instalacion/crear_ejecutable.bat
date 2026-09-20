@echo off
chcp 65001 >nul
echo ============================================
echo  GDEA - Crear ejecutable standalone
echo ============================================
echo.
echo Este script genera una carpeta "dist\GDEA" con un
echo ejecutable que no requiere Python instalado.
echo.
echo REQUISITO: El entorno virtual debe estar configurado
echo (haber ejecutado setup.bat previamente).
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Entorno virtual no encontrado. Ejecute setup.bat primero.
    pause
    exit /b 1
)

:: Instalar PyInstaller si no está
.venv\Scripts\python.exe -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo Instalando PyInstaller...
    .venv\Scripts\python.exe -m pip install pyinstaller --quiet
)

echo Generando ejecutable...
echo (Puede tardar 2-5 minutos)
echo.

.venv\Scripts\python.exe -m PyInstaller ^
    --name GDEA ^
    --onedir ^
    --console ^
    --noconfirm ^
    --hidden-import=fitz ^
    --hidden-import=fitz.fitz ^
    --hidden-import=rich ^
    --hidden-import=rich.console ^
    --hidden-import=rich.prompt ^
    --hidden-import=rich.panel ^
    --hidden-import=rich.table ^
    --hidden-import=rich.progress ^
    --collect-all=fitz ^
    --collect-all=ocrmypdf ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo generar el ejecutable.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Ejecutable creado en: dist\GDEA\
echo.
echo  Para distribuir:
echo    1. Copie la carpeta dist\GDEA completa al USB
echo    2. En el equipo destino, ejecute GDEA\GDEA.exe
echo    3. No requiere Python instalado
echo.
echo  NOTA: La carpeta pesa aproximadamente 200-400 MB.
echo ============================================
pause
