# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 5: Listado de archivos embebidos (CSV).

Un registro por archivo embebido con datos del documento que lo contiene:
  numero_de_orden, numero_de_documento, fecha_documento,
  nombre_archivo_embebido, tamaño_bytes
"""
import csv
from pathlib import Path
from typing import List

from ..core.models import Documento

_CAMPOS = [
    "numero_de_orden",
    "numero_de_documento",
    "fecha_documento",
    "nombre_archivo_embebido",
    "tamaño",
]


def _formatear_tamaño(n: int) -> str:
    """Convierte bytes a la unidad más apropiada con su sigla."""
    if n < 1024:
        return f"{n} bytes"
    n_f = n / 1024
    if n_f < 1024:
        return f"{n_f:.2f} KB"
    n_f /= 1024
    if n_f < 1024:
        return f"{n_f:.2f} MB"
    n_f /= 1024
    if n_f < 1024:
        return f"{n_f:.2f} GB"
    return f"{n_f / 1024:.2f} TB"


def generar_listado_embebidos(documentos: List[Documento], output_dir: str) -> str:
    """Genera listado_embebidos.csv en output_dir. Devuelve la ruta del archivo."""
    salida = Path(output_dir) / "listado_embebidos.csv"

    docs_con_embebidos = [d for d in documentos if d.cantidad_embebidos > 0]

    with open(salida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_CAMPOS)
        writer.writeheader()

        for doc in docs_con_embebidos:
            for embebido in doc.embebidos:
                writer.writerow(
                    {
                        "numero_de_orden": doc.numero_orden,
                        "numero_de_documento": doc.codigo,
                        "fecha_documento": doc.fecha_documento,
                        "nombre_archivo_embebido": embebido.nombre,
                        "tamaño": _formatear_tamaño(len(embebido.data)),
                    }
                )

    return str(salida)
