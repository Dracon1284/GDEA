@echo off
chcp 65001 >nul
echo ============================================
echo  GDEA - Instalacion sin internet (offline)
echo ============================================
echo.

:: Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado.
    echo Instale Python 3.8 o superior y asegurese de marcar
    echo "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

:: Verificar que exista la carpeta de wheels
if not exist "wheels" (
    echo [ERROR] No se encontro la carpeta "wheels".
    echo Este script debe ejecutarse desde la carpeta del programa
    echo que contiene la subcarpeta "wheels".
    pause
    exit /b 1
)

echo [1/2] Creando entorno virtual...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

echo [2/2] Instalando dependencias desde archivos locales...
.venv\Scripts\pip install --no-index --find-links wheels -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ADVERTENCIA] Algunas dependencias no se instalaron.
    echo El programa puede funcionar igual si PyMuPDF y Rich estan presentes.
)

echo.
echo Verificando instalacion...
.venv\Scripts\python -c "import fitz; import rich; print('  PyMuPDF y Rich: OK')"
.venv\Scripts\python -c "import ocrmypdf; print('  ocrmypdf: OK')" 2>nul || echo   ocrmypdf: No disponible ^(OCR desactivado, es opcional^)

echo.
echo ============================================
echo  Instalacion completada.
echo  Ejecute run.bat para iniciar el programa.
echo ============================================
pause
