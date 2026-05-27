@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  GDEA - Instalacion en este equipo
echo ============================================
echo.

:: Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado.
    echo.
    echo Instale Python 3.8 o superior y asegurese de marcar
    echo la opcion "Add Python to PATH" durante la instalacion.
    echo.
    echo Si ya tiene el instalador en este USB, ejecútelo primero
    echo y luego vuelva a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Python encontrado: %%v
echo.

:: Verificar que exista la carpeta wheels
if not exist "wheels" (
    echo [ERROR] No se encontro la carpeta "wheels".
    echo Asegurese de ejecutar este archivo desde la carpeta
    echo que contiene la subcarpeta "wheels".
    pause
    exit /b 1
)

:: Crear entorno virtual
echo [1/2] Creando entorno virtual...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

:: Instalar dependencias desde wheels locales
echo [2/2] Instalando dependencias (sin internet)...
.venv\Scripts\pip install --no-index --find-links wheels -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ADVERTENCIA] Algunas dependencias no se instalaron.
    echo Verificando cuales estan disponibles...
)

:: Verificar instalacion
echo.
echo Verificando...
.venv\Scripts\python -c "import fitz; import rich; print('  PyMuPDF y Rich: OK')"
if %errorlevel% neq 0 (
    echo [ERROR] Las dependencias principales no se instalaron correctamente.
    pause
    exit /b 1
)
.venv\Scripts\python -c "import ocrmypdf; print('  ocrmypdf: OK')" 2>nul || echo   ocrmypdf: No disponible (OCR desactivado, es opcional)

echo.
echo ============================================
echo  Instalacion completada correctamente.
echo.
echo  Para iniciar el programa: ejecute run.bat
echo ============================================
pause
