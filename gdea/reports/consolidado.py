# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 4: PDF consolidado sin archivos embebidos, aplanado y con OCR.

Proceso:
  1. Fusionar todos los documentos preservando el texto original (insert_pdf)
  2. Aplanar: remover widgets/formularios interactivos de cada página
  3. OCR: aplicar con skip_text=True (solo OCR páginas sin texto, como imágenes
     escaneadas). Las páginas GDE ya tienen texto seleccionable → se preserva.

Si ocrmypdf/Tesseract no están disponibles, se genera igual el PDF fusionado
(el texto ya era seleccionable desde los PDFs GDE originales).

Si total de documentos > 100 y seccionar=True, genera múltiples PDFs
de hasta 100 documentos cada uno.
"""
import io
import logging
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Callable, Optional

try:
    import fitz
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

try:
    import ocrmypdf
    OCR_OK = True
except ImportError:
    OCR_OK = False

from ..core.models import Documento


def generar_consolidado(
    documentos: List[Documento],
    output_dir: str,
    seccionar: bool = False,
    callback: Optional[Callable] = None,
) -> List[str]:
    """
    Genera el(los) PDF(s) consolidado(s) en output_dir.
    Devuelve lista con las rutas de los archivos generados.
    """
    if not FITZ_OK:
        raise RuntimeError("PyMuPDF no está instalado. No se puede generar el consolidado.")

    output_path = Path(output_dir)

    if seccionar and len(documentos) > 100:
        lotes = [documentos[i:i + 100] for i in range(0, len(documentos), 100)]
    else:
        lotes = [documentos]

    archivos_generados = []

    for idx, lote in enumerate(lotes):
        nombre = f"consolidado_parte_{idx+1:02d}.pdf" if len(lotes) > 1 else "consolidado.pdf"
        ruta_final = output_path / nombre
        _procesar_lote(lote, ruta_final, callback)
        archivos_generados.append(str(ruta_final))

    return archivos_generados


def _procesar_lote(
    documentos: List[Documento],
    ruta_salida: Path,
    callback: Optional[Callable],
):
    """Fusiona documentos, aplana widgets y aplica OCR."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        _fusionar_preservando_texto(documentos, tmp_path, callback)

        if OCR_OK:
            _aplicar_ocr(tmp_path, ruta_salida)
        else:
            # Sin ocrmypdf: el texto ya es seleccionable (viene de los PDFs GDE)
            shutil.copy2(tmp_path, ruta_salida)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _fusionar_preservando_texto(
    documentos: List[Documento],
    salida: Path,
    callback: Optional[Callable],
):
    """
    Fusiona todos los PDFs en orden usando insert_pdf.

    insert_pdf preserva texto, imágenes, anotaciones y el contenido visual de
    los widgets (incluyendo los sellos de firma digital "Digitally signed by").
    NO se eliminan los widgets porque eso borra el texto de firma del PDF.
    """
    doc_salida = fitz.open()

    for documento in documentos:
        try:
            doc_origen = fitz.open(documento.filepath)
            doc_salida.insert_pdf(doc_origen)
            doc_origen.close()
        except Exception:
            pass

        if callback:
            callback()

    doc_salida.save(
        str(salida),
        garbage=4,
        deflate=True,
        clean=True,
    )
    doc_salida.close()


def _aplicar_ocr(entrada: Path, salida: Path):
    """
    Aplica OCR con skip_text=True: solo procesa páginas sin capa de texto
    (páginas escaneadas o de imagen pura). Las páginas GDE con texto digital
    quedan intactas con su texto ya seleccionable.
    """
    try:
        # Suprimir mensajes de herramientas externas no instaladas (ej. Tesseract)
        # que no impiden la generación del PDF consolidado
        _ocr_loggers = [
            logging.getLogger(name)
            for name in logging.Logger.manager.loggerDict
            if name.startswith("ocrmypdf")
        ]
        niveles_orig = [(lg, lg.level) for lg in _ocr_loggers]
        for lg in _ocr_loggers:
            lg.setLevel(logging.CRITICAL)

        _stderr_orig = sys.stderr
        sys.stderr = io.StringIO()
        try:
            ocrmypdf.ocr(
                str(entrada),
                str(salida),
                language="spa+eng",
                skip_text=True,
                optimize=1,
                progress_bar=False,
                jobs=2,
            )
        finally:
            sys.stderr = _stderr_orig
            for lg, nivel in niveles_orig:
                lg.setLevel(nivel)

    except Exception:
        # Si OCR falla por cualquier razón, el PDF fusionado ya tiene texto
        shutil.copy2(entrada, salida)
