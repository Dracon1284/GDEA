# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Firmante:
    nombre: str = ""
    cuit: str = ""
    cargo: str = ""
    area: str = ""
    fecha_firma: str = ""


@dataclass
class Destinatario:
    tipo: str = ""   # "A" o "COPIA A"
    nombre: str = ""
    area: str = ""


@dataclass
class ArchivoEmbebido:
    nombre: str = ""
    data: bytes = field(default_factory=bytes)
    extension: str = ""


@dataclass
class Documento:
    numero_orden: str = ""
    tipo: str = ""        # IF, ME, NO, PV, SC, etc.
    codigo: str = ""      # Ej: IF-2020-00252349-AFIP-ADLARI%SDGOAI
    filepath: str = ""

    fecha_documento: str = ""
    referencia: str = ""
    cantidad_paginas: int = 0

    firmantes: List[Firmante] = field(default_factory=list)
    destinatarios: List[Destinatario] = field(default_factory=list)
    embebidos: List[ArchivoEmbebido] = field(default_factory=list)

    texto_completo: str = ""

    error: str = ""   # Mensaje de error si el análisis falló

    @property
    def ultimo_firmante(self) -> Optional[Firmante]:
        return self.firmantes[-1] if self.firmantes else None

    @property
    def cantidad_embebidos(self) -> int:
        return len(self.embebidos)

    @property
    def cantidad_firmantes(self) -> int:
        return len(self.firmantes)

    @property
    def es_caratula(self) -> bool:
        return self.tipo == "PV"
