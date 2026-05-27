# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 5: Registro de firmantes (CSV).

Un registro por cada firmante de cada documento:
  numero_de_orden, codigo_documento, fecha_documento,
  nombre_firmante, fecha_firma, cargo_firmante, area_firmante
"""
import csv
from pathlib import Path
from typing import List

from ..core.models import Documento

_CAMPOS = [
    "numero_de_orden",
    "codigo_documento",
    "fecha_documento",
    "nombre_firmante",
    "fecha_firma",
    "cargo_firmante",
    "area_firmante",
]


def generar_firmantes(documentos: List[Documento], output_dir: str) -> str:
    """Genera firmantes.csv en output_dir. Devuelve la ruta del archivo."""
    salida = Path(output_dir) / "firmantes.csv"

    with open(salida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_CAMPOS)
        writer.writeheader()

        for doc in documentos:
            for firmante in doc.firmantes:
                writer.writerow(
                    {
                        "numero_de_orden": doc.numero_orden,
                        "codigo_documento": doc.codigo,
                        "fecha_documento": doc.fecha_documento,
                        "nombre_firmante": firmante.nombre.upper(),
                        "fecha_firma": firmante.fecha_firma,
                        "cargo_firmante": firmante.cargo,
                        "area_firmante": firmante.area,
                    }
                )

    return str(salida)
