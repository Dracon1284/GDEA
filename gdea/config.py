# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
import json
import sys
from pathlib import Path

# Cuando se compila con PyInstaller, sys.executable apunta al .exe
# En ejecución normal, usamos la ubicación de main.py (parent.parent de config.py)
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys.executable).parent
else:
    _BASE_DIR = Path(__file__).parent.parent

_CONFIG_FILE = _BASE_DIR / "gdea_config.json"
_MARKER_FILENAME = "log.txt"

VERSION = "1.3.0"

# Definición de los reportes disponibles (el orden define su numeración en el menú)
REPORTES = {
    "excel": {
        "numero": 1,
        "nombre": "Reporte Excel (XLSX)",
        "descripcion": "Resumen, índice, firmantes, destinatarios y embebidos en hojas de un .xlsx",
        "enabled": True,
    },
    "caratula_y_orden": {
        "numero": 2,
        "nombre": "Carátula y orden del expediente (TXT)",
        "descripcion": "Datos del PV carátula + resumen estadístico + verificación de orden cronológico",
        "enabled": True,
    },
    "indice": {
        "numero": 3,
        "nombre": "Índice de documentos (CSV)",
        "descripcion": "Registro por documento con datos del último firmante",
        "enabled": True,
    },
    "firmantes": {
        "numero": 4,
        "nombre": "Registro de firmantes (CSV)",
        "descripcion": "Un registro por firmante de cada documento",
        "enabled": True,
    },
    "destinatarios": {
        "numero": 5,
        "nombre": "Destinatarios ME/NO (CSV)",
        "descripcion": "Registro de destinatarios en documentos tipo ME y NO",
        "enabled": True,
    },
    "listado_embebidos": {
        "numero": 6,
        "nombre": "Listado de archivos embebidos (CSV)",
        "descripcion": "Un registro por archivo embebido con datos del documento contenedor",
        "enabled": True,
    },
    "embebidos": {
        "numero": 7,
        "nombre": "Extracción de archivos embebidos",
        "descripcion": "Subcarpetas con archivos embebidos (anidadas si es necesario)",
        "enabled": True,
    },
    "consolidado": {
        "numero": 8,
        "nombre": "Consolidado sin embebidos (PDF)",
        "descripcion": "Todos los documentos unificados, aplanados y con OCR",
        "enabled": True,
    },
    "consolidado_txt": {
        "numero": 9,
        "nombre": "Texto consolidado sin embebidos (TXT)",
        "descripcion": "Todos los documentos unificados en texto plano con encabezados",
        "enabled": True,
    },
    "extraer_documentos": {
        "numero": 10,
        "nombre": "Extracción de documentos",
        "descripcion": "Conserva los PDFs individuales del expediente en la carpeta 'documentos'",
        "enabled": True,
    },
}


def cargar_config() -> dict:
    """Carga la configuración de reportes habilitados desde archivo."""
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                guardado = json.load(f)
                # Merge: usar valores guardados, mantener defaults para claves nuevas
                for key in REPORTES:
                    if key in guardado:
                        REPORTES[key]["enabled"] = bool(guardado[key])
        except Exception:
            pass
    return {k: v["enabled"] for k, v in REPORTES.items()}


def guardar_config(config: dict):
    """Persiste el estado habilitado/deshabilitado de cada reporte."""
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def verificar_marker(output_dir: str) -> tuple:
    """Verifica si el directorio ya fue procesado (existe log.txt). Devuelve (existe, info_str)."""
    log_path = Path(output_dir) / _MARKER_FILENAME
    if log_path.exists():
        try:
            contenido = log_path.read_text(encoding="utf-8-sig")
            info_lineas = [
                l.strip()
                for l in contenido.splitlines()
                if l.strip() and not l.strip().startswith("=") and "GDEA —" not in l
            ]
            return True, "\n".join(info_lineas)
        except Exception:
            return True, "(sin información)"
    return False, ""
