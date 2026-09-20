# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
import zipfile
from pathlib import Path
from typing import Tuple, List

from ..config import CARPETA_DOCUMENTOS


def clasificar_zip(zip_path: str) -> str:
    """
    Determina el tipo de ZIP según su nombre de archivo.

    Retorna:
      'EX'       — el stem comienza con 'EX-'
      'DOC_EX'   — el stem comienza con 'Documentos-Ex-'  (mismo tratamiento que EX)
      'GENERICO' — cualquier otro nombre; requiere validación adicional de contenido
    """
    stem = Path(zip_path).stem.upper()
    if stem.startswith("EX-"):
        return "EX"
    if stem.startswith("DOCUMENTOS-EX-") or stem.startswith("DOCUMENTOS-EX "):
        return "DOC_EX"
    return "GENERICO"


def validar_zip(zip_path: str) -> Tuple[bool, str]:
    """
    Valida que el archivo ZIP sea procesable.

    Acepta tres casos:
      · EX-*           → expediente GDE estándar
      · Documentos-Ex-* → misma validez que EX-
      · Cualquier otro  → válido solo si el ZIP contiene únicamente archivos PDF
    """
    path = Path(zip_path)

    if not path.exists():
        return False, f"El archivo '{zip_path}' no existe."
    if not path.is_file():
        return False, f"'{zip_path}' no es un archivo."
    if path.suffix.lower() != ".zip":
        return False, "El archivo debe tener extensión .zip"
    if not zipfile.is_zipfile(zip_path):
        return False, "El archivo no es un ZIP válido."

    tipo = clasificar_zip(zip_path)
    if tipo == "GENERICO":
        ok, err = _validar_solo_pdfs(zip_path)
        if not ok:
            return False, err

    return True, ""


def _validar_solo_pdfs(zip_path: str) -> Tuple[bool, str]:
    """
    Para ZIPs genéricos: verifica que el contenido sea únicamente archivos PDF.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        archivos = [m for m in zf.infolist() if not m.is_dir()]
        if not archivos:
            return False, "El ZIP no contiene archivos."
        no_pdfs = [
            m.filename for m in archivos
            if not m.filename.lower().endswith(".pdf")
        ]
        if no_pdfs:
            primeros = no_pdfs[:3]
            resto = f" y {len(no_pdfs) - 3} más" if len(no_pdfs) > 3 else ""
            return False, (
                f"El ZIP contiene archivos que no son PDF: "
                f"{', '.join(primeros)}{resto}. "
                f"Para procesar un ZIP sin prefijo 'EX-' debe contener únicamente PDFs."
            )
        pdfs = [m for m in archivos if m.filename.lower().endswith(".pdf")]
        if not pdfs:
            return False, "No se encontraron archivos PDF en el ZIP."
    return True, ""


def pdfs_tienen_prefijo_orden(pdfs: List[str]) -> bool:
    """
    Verifica si la mayoría de los PDFs tienen prefijo numérico de 4 dígitos.
    Retorna True si al menos la mitad de los primeros 10 PDFs lo tienen.
    """
    if not pdfs:
        return False
    muestra = pdfs[:10]
    con_prefijo = 0
    for pdf_path in muestra:
        try:
            int(Path(pdf_path).name[:4])
            con_prefijo += 1
        except ValueError:
            pass
    return con_prefijo >= max(1, len(muestra) // 2)


def extraer_zip(zip_path: str, output_dir: str) -> str:
    """Extrae el ZIP en output_dir/Documentos. Devuelve la ruta de extracción."""
    extract_path = Path(output_dir) / CARPETA_DOCUMENTOS
    extract_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Extraer preservando la estructura interna
        for member in zf.infolist():
            # Decodificar nombres en CP437/Latin-1 si es necesario
            try:
                nombre = member.filename.encode("cp437").decode("utf-8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                nombre = member.filename
            member.filename = nombre
            zf.extract(member, extract_path)

    return str(extract_path)


def _glob_pdfs_unicos(carpeta: Path) -> List[Path]:
    """Recolecta PDFs de una carpeta eliminando duplicados (case-insensitive en Windows)."""
    vistos: set = set()
    pdfs: List[Path] = []
    for patron in ("*.pdf", "*.PDF", "*.Pdf"):
        for p in carpeta.glob(patron):
            clave = p.resolve()
            if clave not in vistos:
                vistos.add(clave)
                pdfs.append(p)
    return pdfs


def obtener_pdfs(carpeta: str) -> List[str]:
    """Devuelve lista ordenada de PDFs por número de orden (primeros 4 caracteres).

    Usa resolve() para deduplicar antes de ordenar: en Windows, glob("*.pdf") y
    glob("*.PDF") devuelven los mismos archivos dos veces por el sistema de
    archivos case-insensitive, lo que causaría que cada documento se procese doble.
    """
    pdfs = _glob_pdfs_unicos(Path(carpeta))

    def clave_orden(p: Path) -> int:
        try:
            return int(p.name[:4])
        except ValueError:
            return 9999

    return [str(p) for p in sorted(pdfs, key=clave_orden)]


def obtener_pdfs_sin_orden(carpeta: str) -> List[str]:
    """
    Para ZIPs genéricos cuyos PDFs no tienen prefijo numérico de orden.
    Devuelve lista ordenada alfabéticamente por nombre de archivo.
    """
    pdfs = _glob_pdfs_unicos(Path(carpeta))
    return [str(p) for p in sorted(pdfs, key=lambda p: p.name.lower())]
