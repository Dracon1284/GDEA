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
_MARKER_FILENAME = ".gdea_procesado"

VERSION = "1.2.0"

# Definición de los reportes disponibles
REPORTES = {
    "caratula": {
        "numero": 1,
        "nombre": "Carátula del expediente (TXT)",
        "descripcion": "Datos del PV carátula + total de documentos/embebidos + timestamp",
        "enabled": True,
    },
    "indice": {
        "numero": 2,
        "nombre": "Índice de documentos (CSV)",
        "descripcion": "Registro por documento con datos del último firmante",
        "enabled": True,
    },
    "firmantes": {
        "numero": 3,
        "nombre": "Registro de firmantes (CSV)",
        "descripcion": "Un registro por firmante de cada documento",
        "enabled": True,
    },
    "destinatarios": {
        "numero": 4,
        "nombre": "Destinatarios ME/NO (CSV)",
        "descripcion": "Registro de destinatarios en documentos tipo ME y NO",
        "enabled": True,
    },
    "listado_embebidos": {
        "numero": 5,
        "nombre": "Listado de archivos embebidos (CSV)",
        "descripcion": "Un registro por archivo embebido con datos del documento contenedor",
        "enabled": True,
    },
    "embebidos": {
        "numero": 6,
        "nombre": "Extracción de archivos embebidos",
        "descripcion": "Subcarpetas con archivos embebidos (anidadas si es necesario)",
        "enabled": True,
    },
    "consolidado": {
        "numero": 7,
        "nombre": "PDF consolidado sin embebidos (OCR)",
        "descripcion": "Todos los documentos unificados, aplanados y con OCR",
        "enabled": True,
    },
    "consolidado_txt": {
        "numero": 8,
        "nombre": "Texto consolidado sin embebidos (TXT)",
        "descripcion": "Todos los documentos unificados en texto plano con encabezados",
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


def crear_marker(output_dir: str, zip_filename: str):
    """Crea archivo marcador en el directorio de salida."""
    from datetime import datetime
    marker_path = Path(output_dir) / _MARKER_FILENAME
    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(f"zip={zip_filename}\n")
        f.write(f"fecha={datetime.now().isoformat()}\n")


def verificar_marker(output_dir: str) -> tuple:
    """Verifica si el directorio ya fue procesado. Devuelve (existe, info_str)."""
    marker_path = Path(output_dir) / _MARKER_FILENAME
    if marker_path.exists():
        try:
            contenido = marker_path.read_text(encoding="utf-8")
            return True, contenido.strip()
        except Exception:
            return True, "(sin información)"
    return False, ""
