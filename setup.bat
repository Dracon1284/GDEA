@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  GDEA - Configuracion del entorno
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Instale Python 3.8 o superior desde https://python.org
    pause
    exit /b 1
)

echo [1/3] Creando entorno virtual...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

echo [2/3] Instalando dependencias...
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] Algunas dependencias no se instalaron correctamente.
    echo Verifique que Tesseract este instalado para habilitar OCR:
    echo   https://github.com/UB-Mannheim/tesseract/wiki
)

echo [3/3] Verificando instalacion...
.venv\Scripts\python -c "import fitz; import rich; print('  PyMuPDF y Rich: OK')"
.venv\Scripts\python -c "import ocrmypdf; print('  ocrmypdf: OK')" 2>nul || echo   ocrmypdf: No disponible ^(OCR desactivado^)

echo.
echo ============================================
echo  Configuracion completada.
echo  Ejecute run.bat para iniciar el programa.
echo ============================================
pause
