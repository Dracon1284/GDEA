@echo off
chcp 65001 >nul
echo ============================================
echo  GDEA - Descarga de dependencias (offline)
echo ============================================
echo.
echo Este script descarga todos los paquetes necesarios
echo para poder instalar GDEA sin conexion a internet.
echo.

:: Verificar que el entorno virtual exista (setup.bat debe haber corrido antes)
if not exist ".venv\Scripts\pip.exe" (
    echo [ERROR] Entorno virtual no encontrado.
    echo Primero ejecute setup.bat para crear el entorno.
    pause
    exit /b 1
)

:: Crear carpeta de wheels
if not exist "wheels" mkdir wheels

echo Descargando paquetes...
echo (Esto puede tardar varios minutos dependiendo de la conexion)
echo.

.venv\Scripts\pip download -r requirements.txt -d wheels

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudieron descargar todas las dependencias.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Descarga completada.
echo.
echo  Para instalar en un equipo sin internet:
echo    1. Copie toda esta carpeta a un USB
echo    2. En el equipo destino, instale Python
echo       (incluyalo en el USB: python.org/downloads)
echo    3. Ejecute setup_offline.bat
echo ============================================
pause
