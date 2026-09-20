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

VERSION = "1.4"

CARPETA_DOCUMENTOS = "Documentos"
CARPETA_EMBEBIDOS = "Embebidos"


def nombre_carpeta_salida(output_dir: str) -> str:
    """Nombre de la carpeta de salida del expediente (p. ej. EX-2025-00012345)."""
    return Path(output_dir).name.strip() or "expediente"


def ruta_reporte(output_dir: str, titulo: str, extension: str) -> Path:
    """
    Nombre de archivo de reporte: 'Titulo ' + carpeta de salida + extensión.
    El título ya va con mayúscula inicial (p. ej. Indice, Log, Consolidado).
    """
    ext = extension if extension.startswith(".") else f".{extension}"
    return Path(output_dir) / f"{titulo} {nombre_carpeta_salida(output_dir)}{ext}"

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
        "descripcion": "Conserva los PDFs individuales del expediente en la carpeta 'Documentos'",
        "enabled": True,
    },
}

# Reportes que el bloque superior de Opciones muestra como resultado (sin extraer_documentos)
REPORTES_VISIBLES = tuple(k for k in REPORTES if k != "extraer_documentos")
REPORTES_TABULARES = (
    "caratula_y_orden", "indice", "firmantes", "destinatarios", "listado_embebidos",
)

OPCIONES = {
    "reporte": {
        "numero": "1",
        "nombre": "Reporte",
        "descripcion": "Resumen, índice, firmantes, destinatarios, embebidos y orden de documentos",
    },
    "consolidado": {
        "numero": "2",
        "nombre": "Consolidado sin embebidos",
        "descripcion": "Todos los documentos unificados en un solo archivo sin archivos embebidos",
    },
    "embebidos": {
        "numero": "3",
        "nombre": "Extracción de archivos embebidos",
        "descripcion": "Subcarpetas con archivos embebidos (anidadas si es necesario)",
    },
    "documentos": {
        "numero": "4",
        "nombre": "Extracción de documentos",
        "descripcion": "Conserva los PDFs individuales del expediente en la carpeta 'Documentos'",
    },
}

MODOS = {
    "A": {
        "nombre": "Excel (XLSX)",
        "descripcion": "Activa Reporte Excel (XLSX) y Consolidado sin embebidos (PDF)",
    },
    "B": {
        "nombre": "CSV & Txt",
        "descripcion": "Activa reportes de documentos CSV y Txt",
    },
    "C": {
        "nombre": "Excel CSV & Txt",
        "descripcion": "Activa los reportes de modo A y B",
    },
}

_MODO_DEFAULT = "A"
_OPCIONES_DEFAULT = {k: True for k in OPCIONES}


def resolver_reportes(modo: str, opciones: dict) -> dict:
    """Calcula qué reportes se generan según modo + opciones 1-4."""
    flags = {k: False for k in REPORTES}
    flags["embebidos"] = bool(opciones.get("embebidos", True))
    flags["extraer_documentos"] = bool(opciones.get("documentos", True))
    opt1 = bool(opciones.get("reporte", True))
    opt2 = bool(opciones.get("consolidado", True))
    modo = (modo or _MODO_DEFAULT).upper()
    if modo in ("A", "C") and opt1:
        flags["excel"] = True
    if modo in ("A", "C") and opt2:
        flags["consolidado"] = True
    if modo in ("B", "C") and opt1:
        for key in REPORTES_TABULARES:
            flags[key] = True
    if modo in ("B", "C") and opt2:
        flags["consolidado_txt"] = True
    return flags


def hay_reportes_activos(config: dict) -> bool:
    return any(config.get(k) for k in REPORTES)


def cargar_config() -> dict:
    """Carga modo, opciones y reportes resultantes desde archivo."""
    modo = _MODO_DEFAULT
    opciones = dict(_OPCIONES_DEFAULT)
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                guardado = json.load(f)
            modo_g = str(guardado.get("modo", "")).upper()
            if modo_g in MODOS:
                modo = modo_g
            ops_g = guardado.get("opciones")
            if isinstance(ops_g, dict):
                for key in OPCIONES:
                    if key in ops_g:
                        opciones[key] = bool(ops_g[key])
            else:
                if "embebidos" in guardado:
                    opciones["embebidos"] = bool(guardado["embebidos"])
                if "extraer_documentos" in guardado:
                    opciones["documentos"] = bool(guardado["extraer_documentos"])
        except Exception:
            pass

    flags = resolver_reportes(modo, opciones)
    for key, valor in flags.items():
        REPORTES[key]["enabled"] = valor
    return {"modo": modo, "opciones": opciones, **flags}


def guardar_config(config: dict):
    """Persiste modo, opciones y el estado resultante de cada reporte."""
    modo = str(config.get("modo", _MODO_DEFAULT)).upper()
    if modo not in MODOS:
        modo = _MODO_DEFAULT
    opciones = dict(_OPCIONES_DEFAULT)
    ops = config.get("opciones")
    if isinstance(ops, dict):
        for key in OPCIONES:
            if key in ops:
                opciones[key] = bool(ops[key])
    flags = resolver_reportes(modo, opciones)
    salida = {"modo": modo, "opciones": opciones, **flags}
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(salida, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    config.clear()
    config.update(salida)


def verificar_marker(output_dir: str) -> tuple:
    """Verifica si el directorio ya fue procesado (existe el log). Devuelve (existe, info_str)."""
    candidatos = [
        ruta_reporte(output_dir, "Log", ".txt"),
        Path(output_dir) / "log.txt",
    ]
    log_path = next((p for p in candidatos if p.exists()), None)
    if log_path:
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
