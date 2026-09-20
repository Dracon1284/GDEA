# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 2: Índice de documentos (CSV).

Campos por registro:
  numero_de_orden, numero_de_documento, fecha_documento, referencia,
  cantidad_de_paginas, cantidad_de_archivos_embebidos,
  cantidad_de_firmantes,
  nombre_UF, cargo_UF, area_UF
  (UF = Último Firmante)
"""
import csv
from typing import List

from ..config import ruta_reporte
from ..core.models import Documento

_CAMPOS = [
    "numero_de_orden",
    "numero_de_documento",
    "fecha_documento",
    "referencia",
    "cantidad_de_paginas",
    "cantidad_de_archivos_embebidos",
    "cantidad_de_firmantes",
    "nombre_UF",
    "cargo_UF",
    "area_UF",
]


def generar_indice(documentos: List[Documento], output_dir: str) -> str:
    """Genera Indice <carpeta>.csv en output_dir. Devuelve la ruta del archivo."""
    salida = ruta_reporte(output_dir, "Indice", ".csv")

    with open(salida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_CAMPOS)
        writer.writeheader()

        for doc in documentos:
            uf = doc.ultimo_firmante
            writer.writerow(
                {
                    "numero_de_orden": doc.numero_orden,
                    "numero_de_documento": doc.codigo,
                    "fecha_documento": doc.fecha_documento,
                    "referencia": doc.referencia,
                    "cantidad_de_paginas": doc.cantidad_paginas,
                    "cantidad_de_archivos_embebidos": doc.cantidad_embebidos,
                    "cantidad_de_firmantes": doc.cantidad_firmantes,
                    "nombre_UF": uf.nombre.upper() if uf else "",
                    "cargo_UF": uf.cargo if uf else "",
                    "area_UF": uf.area if uf else "",
                }
            )

    return str(salida)
