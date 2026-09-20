# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 3: Extracción de archivos embebidos.

Estructura de salida:
  output_dir/
    Embebidos/
      {numero_orden}/          ← carpeta por documento que tiene embebidos
        archivo1.pdf
        archivo2.xlsx
        {numero_orden}-001/    ← si un PDF embebido tiene sus propios embebidos
          ...

Recursivo: si un archivo embebido es PDF y tiene embebidos propios,
se crea una subcarpeta {orden_padre}-{serie} y se procesan de igual forma.
"""
from pathlib import Path
from typing import List

try:
    import fitz
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

from ..config import CARPETA_EMBEBIDOS
from ..core.models import Documento, ArchivoEmbebido


def extraer_todos_embebidos(documentos: List[Documento], output_dir: str) -> str:
    """
    Extrae todos los archivos embebidos a output_dir/Embebidos/.
    Devuelve la ruta de la carpeta de embebidos.
    """
    base = Path(output_dir) / CARPETA_EMBEBIDOS

    docs_con_embebidos = [d for d in documentos if d.cantidad_embebidos > 0]
    if not docs_con_embebidos:
        return str(base)

    base.mkdir(parents=True, exist_ok=True)

    for doc in docs_con_embebidos:
        carpeta_doc = base / doc.numero_orden
        carpeta_doc.mkdir(exist_ok=True)
        _guardar_embebidos(doc.embebidos, carpeta_doc, doc.numero_orden)

    return str(base)


def _guardar_embebidos(
    embebidos: List[ArchivoEmbebido],
    carpeta: Path,
    prefijo: str,
    serie: int = 0,
):
    """
    Guarda la lista de embebidos en carpeta.
    Si algún embebido es PDF con sus propios embebidos, los procesa recursivamente.
    """
    for embebido in embebidos:
        destino = carpeta / embebido.nombre
        # Evitar sobreescribir si hay nombres duplicados
        if destino.exists():
            stem = destino.stem
            ext = destino.suffix
            contador = 1
            while destino.exists():
                destino = carpeta / f"{stem}_{contador}{ext}"
                contador += 1

        destino.write_bytes(embebido.data)

        # Si es PDF, verificar si tiene embebidos propios
        if embebido.extension.lower() == ".pdf" and FITZ_OK:
            sub_embebidos = _leer_embebidos_de_bytes(embebido.data)
            if sub_embebidos:
                serie += 1
                sub_carpeta_nombre = f"{prefijo}-{serie:03d}"
                sub_carpeta = carpeta / sub_carpeta_nombre
                sub_carpeta.mkdir(exist_ok=True)
                _guardar_embebidos(sub_embebidos, sub_carpeta, sub_carpeta_nombre, 0)


def _leer_embebidos_de_bytes(data: bytes) -> List[ArchivoEmbebido]:
    """Abre un PDF desde bytes y extrae sus archivos embebidos."""
    try:
        pdf = fitz.open(stream=data, filetype="pdf")
        embebidos = []
        count = pdf.embfile_count()
        for i in range(count):
            info = pdf.embfile_info(i)
            archivo_data = pdf.embfile_get(i)
            nombre = info.get("filename") or info.get("name") or f"embebido_{i+1}"
            ext = Path(nombre).suffix.lower()
            embebidos.append(ArchivoEmbebido(nombre=nombre, data=archivo_data, extension=ext))
        pdf.close()
        return embebidos
    except Exception:
        return []
