# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 1: Carátula del expediente en formato TXT.

Genera un archivo de texto con:
 - Todo el texto del documento PV carátula
 - Total de documentos en el expediente
 - Total de archivos embebidos
 - Timestamp de generación
"""
from datetime import datetime
from pathlib import Path

from ..core.models import Documento


def generar_caratula(
    doc_caratula: Documento,
    texto_caratula: str,
    total_documentos: int,
    total_embebidos: int,
    output_dir: str,
) -> str:
    """
    Genera caratula.txt en output_dir.
    Devuelve la ruta del archivo generado.
    """
    salida = Path(output_dir) / "caratula.txt"

    lineas = [
        "=" * 70,
        "  GDEA — CARÁTULA DEL EXPEDIENTE",
        "=" * 70,
        "",
        f"Expediente: {doc_caratula.codigo}",
        f"Número de orden: {doc_caratula.numero_orden}",
        "",
        "─" * 70,
        "  CONTENIDO DEL DOCUMENTO CARÁTULA",
        "─" * 70,
        "",
    ]

    # Agregar el texto del PV
    for linea in texto_caratula.splitlines():
        lineas.append(linea)

    lineas += [
        "",
        "─" * 70,
        "  RESUMEN DEL EXPEDIENTE",
        "─" * 70,
        "",
        f"  Total de documentos:         {total_documentos}",
        f"  Total de archivos embebidos: {total_embebidos}",
        "",
        "─" * 70,
        "  LOG DE GENERACIÓN",
        "─" * 70,
        "",
        f"  Generado por:  GDEA v1.0",
        f"  Fecha y hora:  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "=" * 70,
    ]

    salida.write_text("\n".join(lineas), encoding="utf-8-sig")
    return str(salida)
