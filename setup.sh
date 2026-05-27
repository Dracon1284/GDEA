#!/bin/bash
echo "============================================"
echo " GDEA - Configuracion del entorno"
echo "============================================"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no encontrado. Instale Python 3.8 o superior."
    exit 1
fi

echo "[1/3] Creando entorno virtual..."
python3 -m venv .venv

echo "[2/3] Instalando dependencias..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt

echo "[3/3] Verificando instalacion..."
.venv/bin/python -c "import fitz; import rich; print('  PyMuPDF y Rich: OK')"
.venv/bin/python -c "import ocrmypdf; print('  ocrmypdf: OK')" 2>/dev/null || echo "  ocrmypdf: No disponible (OCR desactivado)"

echo ""
echo "Configuracion completada. Ejecute: bash run.sh"
