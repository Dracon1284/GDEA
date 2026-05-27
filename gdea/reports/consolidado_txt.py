# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 8: Texto consolidado sin archivos embebidos (TXT).

Extrae el texto de cada documento del expediente y los unifica en un archivo
de texto plano con encabezados separadores por documento.
"""
from pathlib import Path
from typing import List, Callable, Optional

try:
    import fitz
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

from ..core.models import Documento

_SEP = "=" * 80


def generar_consolidado_txt(
    documentos: List[Documento],
    output_dir: str,
    seccionar: bool = False,
    callback: Optional[Callable] = None,
) -> List[str]:
    """
    Genera el(los) TXT consolidado(s) en output_dir.
    Devuelve lista con las rutas de los archivos generados.
    """
    if not FITZ_OK:
        raise RuntimeError("PyMuPDF no está instalado. No se puede generar el consolidado TXT.")

    output_path = Path(output_dir)

    if seccionar and len(documentos) > 100:
        lotes = [documentos[i:i + 100] for i in range(0, len(documentos), 100)]
    else:
        lotes = [documentos]

    archivos_generados = []

    for idx, lote in enumerate(lotes):
        nombre = f"consolidado_parte_{idx + 1:02d}.txt" if len(lotes) > 1 else "consolidado.txt"
        ruta_final = output_path / nombre
        _procesar_lote(lote, ruta_final, callback)
        archivos_generados.append(str(ruta_final))

    return archivos_generados


def _procesar_lote(
    documentos: List[Documento],
    ruta_salida: Path,
    callback: Optional[Callable],
):
    with open(ruta_salida, "w", encoding="utf-8") as f:
        for documento in documentos:
            _escribir_encabezado(f, documento)
            try:
                doc = fitz.open(documento.filepath)
                for page in doc:
                    texto = page.get_text()
                    if texto.strip():
                        f.write(texto)
                doc.close()
            except Exception:
                f.write("[Error al extraer texto del documento]\n")
            f.write("\n\n")
            if callback:
                callback()


def _escribir_encabezado(f, documento: Documento):
    f.write(_SEP + "\n")

    orden = documento.numero_orden or "????"
    codigo = documento.codigo or "(sin código)"
    f.write(f"DOCUMENTO {orden} — {codigo}\n")

    partes = []
    if documento.tipo:
        partes.append(f"Tipo: {documento.tipo}")
    if documento.fecha_documento:
        partes.append(f"Fecha: {documento.fecha_documento}")
    if documento.cantidad_paginas:
        partes.append(f"Páginas: {documento.cantidad_paginas}")
    if partes:
        f.write("  |  ".join(partes) + "\n")

    if documento.ultimo_firmante:
        uf = documento.ultimo_firmante
        firma_partes = []
        if uf.nombre:
            firma_partes.append(f"Firmante: {uf.nombre}")
        if uf.cargo:
            firma_partes.append(f"Cargo: {uf.cargo}")
        if uf.area:
            firma_partes.append(f"Área: {uf.area}")
        if firma_partes:
            f.write("  |  ".join(firma_partes) + "\n")

    f.write(_SEP + "\n\n")
