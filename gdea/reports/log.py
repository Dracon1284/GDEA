# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Log de generación: archivo log.txt que actúa como marcador de procesamiento.
Reemplaza al antiguo .gdea_procesado con información más completa y legible.
"""
from datetime import datetime
from pathlib import Path
from typing import List

from ..core.models import Documento

_SEP = "=" * 70


def generar_log(
    zip_path: str,
    documentos: List[Documento],
    output_dir: str,
    version: str,
    duracion: float = None,
) -> str:
    """Genera log.txt en output_dir. Devuelve la ruta del archivo generado."""
    salida = Path(output_dir) / "log.txt"
    ahora = datetime.now()

    total_embebidos = sum(d.cantidad_embebidos for d in documentos)

    lineas = [
        _SEP,
        "  GDEA — LOG DE GENERACIÓN",
        _SEP,
        "",
        f"  Programa:           GDEA v{version}",
        f"  Fecha y hora:       {ahora.strftime('%d/%m/%Y %H:%M:%S')}",
        f"  ZIP procesado:      {Path(zip_path).name}",
        f"  Documentos:         {len(documentos)}",
        f"  Archivos embebidos: {total_embebidos}",
    ]
    if duracion is not None:
        lineas.append(f"  Tiempo:             {duracion:.1f} segundos")
    lineas += ["", _SEP]

    salida.write_text("\n".join(lineas), encoding="utf-8-sig")
    return str(salida)
