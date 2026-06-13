# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Reporte 1: Carátula del expediente en formato TXT.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.models import Documento

_SEP_H = "=" * 70
_SEP_L = "─" * 70


def generar_caratula(
    doc_caratula: Documento,
    texto_caratula: str,
    todos_documentos: List[Documento],
    output_dir: str,
) -> str:
    """Genera caratula.txt en output_dir. Devuelve la ruta del archivo generado."""
    salida = Path(output_dir) / "caratula.txt"

    total_docs      = len(todos_documentos)
    total_embebidos = sum(d.cantidad_embebidos for d in todos_documentos)
    total_hojas     = sum(d.cantidad_paginas for d in todos_documentos)
    firma_rec       = _firma_mas_reciente(todos_documentos)
    dias_str        = _calcular_dias(doc_caratula.fecha_documento, firma_rec)
    orden           = _verificar_orden(todos_documentos)

    lineas = [
        _SEP_H,
        "  GDEA — CARÁTULA DEL EXPEDIENTE",
        _SEP_H,
        "",
        f"N° documento:    {doc_caratula.codigo}",
        f"Número de orden: {doc_caratula.numero_orden}",
        "",
        _SEP_L,
        "  RESUMEN DEL EXPEDIENTE",
        _SEP_L,
        "",
        f"  Total de documentos:              {total_docs}",
        f"  Total de archivos embebidos:      {total_embebidos}",
        f"  Total de hojas:                   {total_hojas}",
    ]

    if firma_rec:
        lineas.append(
            f"  Firma más reciente:               {firma_rec['fecha']}  (doc. {firma_rec['orden']})"
        )
    else:
        lineas.append(
            "  Firma más reciente:               (sin firmas detectadas)"
        )

    lineas.append(
        f"  Días carátula → firma más reciente: {dias_str}"
    )

    if orden["ordenado"]:
        lineas.append(
            "  Documentos en orden cronológico:  Sí"
        )
    else:
        lineas.append(
            "  Documentos en orden cronológico:  No (Ver sección ORDEN DOCUMENTOS)"
        )

    lineas += [
        "",
        _SEP_L,
        "  CONTENIDO CARÁTULA",
        _SEP_L,
        "",
    ]

    for linea in texto_caratula.splitlines():
        lineas.append(linea)

    if not orden["ordenado"] and orden["orden_sugerido"]:
        lineas += [
            "",
            _SEP_L,
            "  ORDEN DOCUMENTOS",
            _SEP_L,
            "",
            "  Documentos ordenados por fecha de firma del último firmante (ascendente):",
            "",
            f"  {'Orden':<8}  Fecha firma último firmante",
            f"  {'─' * 6}  {'─' * 28}",
        ]
        for item in orden["orden_sugerido"]:
            lineas.append(f"  {item['orden']:<8}  {item['fecha_firma']}")
        lineas.append("")

    lineas += ["", _SEP_H]

    salida.write_text("\n".join(lineas), encoding="utf-8-sig")
    return str(salida)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_firma(fecha_str: str) -> Optional[datetime]:
    """Parse YYYY.MM.DD HH:MM:SS"""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str.strip(), "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def _parse_doc(fecha_str: str) -> Optional[datetime]:
    """Parse DD/MM/YYYY"""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str.strip(), "%d/%m/%Y")
    except ValueError:
        return None


def _firma_mas_reciente(documentos: List[Documento]) -> Optional[dict]:
    mejor_dt = None
    resultado = None
    for doc in documentos:
        uf = doc.ultimo_firmante
        if not uf or not uf.fecha_firma:
            continue
        dt = _parse_firma(uf.fecha_firma)
        if dt and (mejor_dt is None or dt > mejor_dt):
            mejor_dt = dt
            resultado = {"fecha": uf.fecha_firma, "orden": doc.numero_orden}
    return resultado


def _calcular_dias(fecha_caratula: str, firma_rec: Optional[dict]) -> str:
    if not firma_rec or not fecha_caratula:
        return "(no disponible)"
    dt_car   = _parse_doc(fecha_caratula)
    dt_firma = _parse_firma(firma_rec["fecha"])
    if not dt_car or not dt_firma:
        return "(no disponible)"
    dias = (dt_firma.date() - dt_car.date()).days
    return f"{dias} días"


def _verificar_orden(documentos: List[Documento]) -> dict:
    """
    Verifica si los documentos están en orden cronológico por fecha del último firmante.
    Dos documentos del mismo día se consideran en orden.
    """
    pares = [
        (doc, _parse_firma(doc.ultimo_firmante.fecha_firma))
        for doc in documentos
        if doc.ultimo_firmante and doc.ultimo_firmante.fecha_firma
    ]
    pares = [(doc, dt) for doc, dt in pares if dt is not None]

    if len(pares) <= 1:
        return {"ordenado": True, "orden_sugerido": []}

    fechas = [dt for _, dt in pares]
    es_asc  = all(fechas[i].date() <= fechas[i + 1].date() for i in range(len(fechas) - 1))
    es_desc = all(fechas[i].date() >= fechas[i + 1].date() for i in range(len(fechas) - 1))

    if es_asc or es_desc:
        return {"ordenado": True, "orden_sugerido": []}

    sorted_pares = sorted(pares, key=lambda x: x[1])
    docs_sin_fecha = [
        doc for doc in documentos
        if not (doc.ultimo_firmante and doc.ultimo_firmante.fecha_firma
                and _parse_firma(doc.ultimo_firmante.fecha_firma))
    ]

    orden_sugerido = [
        {"orden": doc.numero_orden, "fecha_firma": doc.ultimo_firmante.fecha_firma}
        for doc, _ in sorted_pares
    ] + [
        {"orden": doc.numero_orden, "fecha_firma": "(sin firma)"}
        for doc in docs_sin_fecha
    ]

    return {"ordenado": False, "orden_sugerido": orden_sugerido}
