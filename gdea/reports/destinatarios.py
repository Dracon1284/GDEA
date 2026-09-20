# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 6: Destinatarios de documentos ME y NO (CSV).

Un registro por destinatario de documentos tipo ME (Memorando) y NO (Nota):
  numero_orden, codigo_documento, fecha_documento,
  tipo_destinatario (A / COPIA A), nombre, area
"""
import csv
from typing import List

from ..config import ruta_reporte
from ..core.models import Documento

_CAMPOS = [
    "numero_orden",
    "codigo_documento",
    "fecha_documento",
    "A_COPIA_A",
    "nombre",
    "area",
]


def generar_destinatarios(documentos: List[Documento], output_dir: str) -> str:
    """Genera Destinatarios <carpeta>.csv en output_dir. Devuelve la ruta del archivo."""
    salida = ruta_reporte(output_dir, "Destinatarios", ".csv")

    docs_me_no = [d for d in documentos if d.tipo in ("ME", "NO")]

    with open(salida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_CAMPOS)
        writer.writeheader()

        for doc in docs_me_no:
            for dest in doc.destinatarios:
                writer.writerow(
                    {
                        "numero_orden": doc.numero_orden,
                        "codigo_documento": doc.codigo,
                        "fecha_documento": doc.fecha_documento,
                        "A_COPIA_A": dest.tipo,
                        "nombre": dest.nombre,
                        "area": dest.area,
                    }
                )

    return str(salida)
