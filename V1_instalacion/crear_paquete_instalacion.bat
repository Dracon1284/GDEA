@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  GDEA - Crear paquete de instalacion
echo ============================================
echo.
echo Genera la carpeta "distribucion\" lista para
echo copiar a un USB e instalar en otro equipo.
echo.

:: Verificar entorno virtual
if not exist ".venv\Scripts\pip.exe" (
    echo [ERROR] Entorno virtual no encontrado.
    echo Ejecute setup.bat primero para crear el entorno.
    pause
    exit /b 1
)

:: Limpiar carpeta anterior
if exist "distribucion" (
    echo Eliminando paquete anterior...
    rmdir /s /q "distribucion"
)
mkdir "distribucion"

:: ── Paso 1: Descargar paquetes ────────────────────────────────────────────
echo [1/3] Descargando paquetes de Python...
echo (Requiere conexion a internet - puede tardar varios minutos)
echo.
mkdir "distribucion\wheels"
.venv\Scripts\pip download -r requirements.txt -d "distribucion\wheels"
if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron descargar los paquetes.
    pause
    exit /b 1
)

:: ── Paso 2: Copiar archivos del proyecto ─────────────────────────────────
echo.
echo [2/3] Copiando archivos del proyecto...

:: Código fuente
xcopy /E /I /Q /EXCLUDE:crear_paquete_instalacion.bat "gdea" "distribucion\gdea"

:: Archivos raíz
copy /Y "main.py"          "distribucion\main.py"          >nul
copy /Y "requirements.txt" "distribucion\requirements.txt" >nul
copy /Y "run.bat"          "distribucion\run.bat"          >nul
copy /Y "INSTALAR.bat"     "distribucion\INSTALAR.bat"     >nul

:: ── Paso 3: Crear ZIP del paquete ─────────────────────────────────────────
echo [3/3] Empaquetando en ZIP...
if exist "GDEA_instalacion.zip" del /Q "GDEA_instalacion.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'distribucion\*' -DestinationPath 'GDEA_instalacion.zip' -Force"
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] No se pudo crear el ZIP (requiere Windows 10+).
    echo El paquete igual esta disponible en la carpeta distribucion\
)

echo.
echo ============================================
echo  Paquete generado correctamente.
echo.
echo  Opciones para distribuir:
echo    A) Copie la carpeta  "distribucion\"   al USB
echo    B) Copie el archivo  "GDEA_instalacion.zip"  al USB
echo.
echo  En el equipo destino:
echo    1. Si usó ZIP: extraiga el contenido en una carpeta
echo    2. Asegurese de tener Python instalado
echo       (version 3.8 o superior, con "Add Python to PATH")
echo    3. Ejecute INSTALAR.bat  (solo la primera vez)
echo    4. Ejecute run.bat  para iniciar el programa
echo ============================================
pause
