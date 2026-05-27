#!/bin/bash
if [ ! -f ".venv/bin/python" ]; then
    echo "Entorno no configurado. Ejecutando setup..."
    bash setup.sh
fi
.venv/bin/python main.py
