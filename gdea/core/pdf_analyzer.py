# -*- coding: utf-8 -*-
"""
Módulo de análisis de PDFs del sistema GDE (Gestión Documental Electrónica Argentina).

Convenciones de nomenclatura GDE:
  Filename: "{orden} - {TIPO}-{AÑO}-{NÚMERO}-{ORGANISMO}-{ÁREA}.pdf"
  Ejemplo:  "0011 - IF-2020-00252349-AFIP-ADLARI%SDGOAI.pdf"

Tipos de documentos:
  IF = Informe (gráfico) — páginas de firma al final
  ME = Memorando        — tiene destinatarios
  NO = Nota             — tiene destinatarios
  PV = Providencia      — puede ser la carátula del expediente
  SC = Sin Clasificar / otros
"""
import re
from pathlib import Path
from typing import List

try:
    import fitz  # PyMuPDF
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

from .models import Documento, Firmante, Destinatario, ArchivoEmbebido

# ─── Juego de caracteres válidos en nombres de firmantes ──────────────────────
# Incluye apóstrofe para nombres como D'ERRICO.
# Se tolera hasta 3 chars fuera de este juego para cubrir artefactos de
# codificación del PDF (ej: SEBASTI?N en lugar de SEBASTIÁN).
_CHARS_NOMBRE_FIRMANTE = frozenset(
    "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
    "ÁÉÍÓÚÜÀÂÃÈÊËÎÏÔÕÙÛÝ"
    " ,.-'"
)

# ─── Patrones de firma digital GDE ────────────────────────────────────────────

_RE_SIGN_START = re.compile(
    r"Digitally signed by\s+(.+?)(?:\n|$)",
    re.IGNORECASE,
)
_RE_DN_LINE = re.compile(
    r"DN\s*:\s*(.+?)(?:\n|$)",
    re.IGNORECASE,
)
_RE_SERIALNUM = re.compile(
    r"(?:SERIALNUMBER|SN)\s*=\s*(?:CUI[LT]\s*)?(\d{11}|\d{2}[-]\d{8}[-]\d)",
    re.IGNORECASE,
)
_RE_OU = re.compile(r"OU\s*=\s*([^,\n]+)", re.IGNORECASE)
_RE_O  = re.compile(r"(?<![A-Z])O\s*=\s*([^,\n]+)", re.IGNORECASE)
_RE_SIGN_DATE = re.compile(
    r"Date\s*:\s*(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})",
    re.IGNORECASE,
)

# Patrón alternativo: firmas en español dentro del cuerpo del documento
_RE_FIRMADO_ES = re.compile(
    r"(?:Firmado\s+(?:digitalmente\s+)?por|FIRMANTE)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ][^\n]{3,60})\n"
    r"(?:.*?(?:CUIL|CUIT)\s*[:\-]?\s*(\d{2}[-.]?\d{8}[-.]?\d)[^\n]*)?"
    r"(?:.*?(?:Cargo|ROL)\s*[:\-]?\s*([^\n]{2,80}))?"
    r"(?:.*?(?:Área|Area|Repartición|ORGANISMO)\s*[:\-]?\s*([^\n]{2,80}))?",
    re.IGNORECASE | re.DOTALL,
)

# ─── Patrones de fecha y referencia ───────────────────────────────────────────

# Formato largo GDE: "(Martes) 16 de Julio de 2019"
_RE_FECHA_LARGA = re.compile(
    r"(?:(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+)?"
    r"(\d{1,2})\s+de\s+"
    r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
    r"\s+de\s+(\d{4})",
    re.IGNORECASE,
)

# Formato con etiqueta: "Fecha Caratulación: 16/07/2019"
_RE_FECHA_LABEL = re.compile(
    r"fecha[^\n:]{0,30}:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    re.IGNORECASE,
)

# Formato numérico: "04/05/2020", "4/5/2020", acepta separadores /, -
# Usa lookbehind/lookahead negativos para no capturar parte de números más largos
_RE_FECHA_NUM = re.compile(
    r"(?<!\d)(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})(?!\d)",
)

_MESES_ES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
}
# Inicio del bloque de referencia. Solo la etiqueta "Referencia:" — se descartan
# "Asunto:" / "RE:" que aparecen en emails embebidos y generan falsos positivos.
_RE_REFERENCIA_INICIO = re.compile(r"^\s*Referencia\s*:\s*(.*)$", re.IGNORECASE)

# Fin del bloque de referencia en documentos ME/NO: inicio de los destinatarios.
_RE_REFERENCIA_FIN = re.compile(r"^\s*(?:A|Con\s+Copia\s+A)\s*:", re.IGNORECASE)

# ─── Patrones de destinatarios (ME / NO) ──────────────────────────────────────

# Detecta la línea de etiqueta "A:" o "Con Copia A:"
_RE_DEST_LABEL = re.compile(
    r"^(A|Con\s+Copia\s+A)\s*:\s*(.*)$",
    re.IGNORECASE,
)

# Detecta líneas que terminan un bloque de destinatarios
_RE_DEST_TERMINATOR = re.compile(
    r"^(?:De\s+(?:mi|su)|Saludo|Producido|N[uú]mero|Referencia|"
    r"A\s*:|Con\s+Copia\s+A\s*:)",
    re.IGNORECASE,
)

# Extrae pares (nombre, area) del formato "APELLIDO, NOMBRE (AREA)"
_RE_DEST_INDIVIDUO = re.compile(
    r"([^,(]+(?:,\s*[^,(]+)?)\s*\(([^)]+)\)",
)


# ─── Funciones públicas ────────────────────────────────────────────────────────

def parsear_nombre_archivo(filename: str) -> dict:
    """
    Extrae metadata del nombre de archivo GDE.
    Devuelve dict con: numero_orden, tipo, codigo
    """
    stem = Path(filename).stem

    partes = stem.split(" - ", 1)
    if len(partes) != 2:
        return {
            "numero_orden": stem[:4].strip() if len(stem) >= 4 else stem,
            "tipo": "DESCONOCIDO",
            "codigo": stem,
        }

    numero_orden = partes[0].strip()
    codigo = partes[1].strip()
    tipo = codigo.split("-")[0] if "-" in codigo else "DESCONOCIDO"

    return {"numero_orden": numero_orden, "tipo": tipo.upper(), "codigo": codigo}


def analizar_pdf(filepath: str, numero_orden_override: str = None) -> Documento:
    """Analiza un PDF GDE y devuelve un Documento con toda la información extraída."""
    filename = Path(filepath).name
    meta = parsear_nombre_archivo(filename)
    if numero_orden_override is not None:
        meta["numero_orden"] = numero_orden_override

    doc = Documento(
        numero_orden=meta["numero_orden"],
        tipo=meta["tipo"],
        codigo=meta["codigo"],
        filepath=filepath,
    )

    if not FITZ_OK:
        doc.error = "PyMuPDF no está instalado"
        return doc

    try:
        pdf = fitz.open(filepath)
        doc.cantidad_paginas = pdf.page_count

        # Extraer archivos embebidos
        doc.embebidos = _extraer_embebidos(pdf)

        # Texto completo del documento
        texto_completo = ""
        for page in pdf:
            texto_completo += page.get_text() + "\n"

        doc.texto_completo = texto_completo
        doc.fecha_documento = _extraer_fecha(texto_completo)
        doc.referencia = _extraer_referencia(texto_completo)
        doc.firmantes = _extraer_firmantes(texto_completo, pdf, meta["tipo"])

        if meta["tipo"] in ("ME", "NO"):
            doc.destinatarios = _extraer_destinatarios(texto_completo)

        pdf.close()

    except Exception as e:
        doc.error = str(e)

    return doc


def es_caratula_expediente(doc: Documento, texto: str) -> bool:
    """Determina si este PV es la carátula del expediente."""
    return doc.tipo == "PV" and "carátula" in texto.lower()


def extraer_texto_completo(filepath: str) -> str:
    """Extrae todo el texto visible de un PDF."""
    if not FITZ_OK:
        return ""
    try:
        pdf = fitz.open(filepath)
        texto = ""
        for page in pdf:
            texto += page.get_text() + "\n"
        pdf.close()
        return texto
    except Exception:
        return ""


# ─── Funciones internas ────────────────────────────────────────────────────────

def _extraer_embebidos(pdf) -> List[ArchivoEmbebido]:
    """Extrae archivos embebidos de un PDF."""
    embebidos = []
    try:
        count = pdf.embfile_count()
        for i in range(count):
            info = pdf.embfile_info(i)
            data = pdf.embfile_get(i)
            nombre = info.get("filename") or info.get("name") or f"embebido_{i+1}"
            ext = Path(nombre).suffix.lower()
            embebidos.append(ArchivoEmbebido(nombre=nombre, data=data, extension=ext))
    except Exception:
        pass
    return embebidos


def _extraer_fecha(texto: str) -> str:
    """
    Extrae la fecha del documento y la normaliza a DD/MM/YYYY.

    Prioridad:
      1. Formato largo GDE: "Martes 16 de Julio de 2019"
      2. Etiqueta numérica: "Fecha Caratulación: 16/07/2019"
      3. Numérico suelto al inicio de línea: "04/05/2020"
    """
    buscar = texto

    # 1. Formato largo con nombre de mes en español
    m = _RE_FECHA_LARGA.search(buscar)
    if m:
        dia = m.group(1).zfill(2)
        mes = _MESES_ES.get(m.group(2).lower(), "??")
        anio = m.group(3)
        return f"{dia}/{mes}/{anio}"

    # 2. "Fecha <etiqueta>: DD/MM/YYYY"
    m = _RE_FECHA_LABEL.search(buscar)
    if m:
        return _normalizar_fecha_num(m.group(1))

    # 3. Fecha numérica sola al inicio de línea
    m = _RE_FECHA_NUM.search(buscar)
    if m:
        return _normalizar_fecha_num(m.group(1))

    return ""


def _normalizar_fecha_num(fecha_str: str) -> str:
    """Normaliza DD/MM/YYYY o DD-MM-YYYY a DD/MM/YYYY con ceros a la izquierda."""
    m = re.match(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", fecha_str.strip())
    if m:
        d, mo, y = m.groups()
        return f"{d.zfill(2)}/{mo.zfill(2)}/{y}"
    return fecha_str


def _extraer_referencia(texto: str) -> str:
    """
    Busca la referencia del documento.

    La referencia GDE puede ocupar varias líneas por el ajuste de línea del PDF.
    Se unen las líneas siguientes hasta encontrar una línea en blanco o el inicio
    del bloque de destinatarios ("A:" / "Con Copia A:", en documentos ME/NO).
    Solo se considera la etiqueta "Referencia:" (no "Asunto:" ni "RE:").
    """
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        m = _RE_REFERENCIA_INICIO.match(linea)
        if not m:
            continue

        partes = []
        primera = m.group(1).strip()
        if primera:
            partes.append(primera)

        for siguiente in lineas[i + 1:]:
            if not siguiente.strip():
                break  # línea en blanco → fin de la referencia
            if _RE_REFERENCIA_FIN.match(siguiente):
                break  # inicio de destinatarios (ME/NO)
            partes.append(siguiente.strip())
            if len(partes) >= 6:
                break  # tope de seguridad

        return _unir_lineas_referencia(partes)[:300]

    return ""


def _unir_lineas_referencia(partes: List[str]) -> str:
    """
    Une las líneas de una referencia multilínea. Normalmente separa con un espacio,
    salvo cuando la línea previa termina en '-' (código o palabra cortada por el
    ajuste de línea, p. ej. 'EX-' + '2024...' → 'EX-2024...'), donde une sin espacio.
    """
    if not partes:
        return ""
    resultado = partes[0]
    for p in partes[1:]:
        if resultado.endswith("-"):
            resultado += p
        else:
            resultado += " " + p
    return resultado.strip()


def _extraer_firmantes(texto: str, pdf, tipo: str) -> List[Firmante]:
    """
    Extrae firmantes digitales del PDF.
    Para IF: busca en las últimas páginas (páginas de firma al final).
    Para otros: busca en todo el texto.
    """
    if tipo == "IF":
        texto_firma = _texto_paginas_firma(pdf)
    else:
        texto_firma = texto

    firmantes = _buscar_firmas_digitally_signed(texto_firma)

    # Fallback: buscar patrón en español si no encontró nada
    if not firmantes:
        firmantes = _buscar_firmas_espanol(texto_firma)

    return firmantes


def _texto_paginas_firma(pdf) -> str:
    """Para documentos IF: extrae texto de las páginas que contienen firmas digitales."""
    paginas_firma = []
    for i in range(pdf.page_count - 1, -1, -1):
        txt = pdf[i].get_text()
        if "Digitally signed" in txt or "Firmado" in txt.lower():
            paginas_firma.append(txt)
        elif paginas_firma:
            break  # Detener al llegar a páginas sin firma

    if paginas_firma:
        return "\n".join(reversed(paginas_firma))

    # Si no encontró páginas de firma separadas, devolver todo el texto
    texto_total = ""
    for page in pdf:
        texto_total += page.get_text() + "\n"
    return texto_total


def _es_sello_sistema(nombre: str) -> bool:
    """Devuelve True si el nombre es un sello del sistema GDE, no un firmante humano."""
    n = nombre.upper().strip()
    return "GESTION DOCUMENTAL" in n or n.startswith("GDE ") or n == "GDE"


def _buscar_firmas_digitally_signed(texto: str) -> List[Firmante]:
    """
    Extrae firmantes del patrón estándar 'Digitally signed by'.

    GDE tiene tres variantes:

    Variante A — firmante humano directo (IF):
        Digitally signed by APELLIDO Nombres Nombres
        Date: 2020.05.05 08:51:12 ART
        Location: Ciudad Autónoma de Buenos Aires
        APELLIDO, NOMBRES NOMBRES
        Cargo
        Area
        Organismo...

    Variante B — sello GDE con firmante humano embebido (PV/ME/NO):
        Digitally signed by GDE AFIP
        DN: cn=GDE AFIP, ..., serialNumber=CUIT 23373624349
        Date: 2019.07.16 15:22:24 -03'00'
        SOTO, DAMIAN PATRICIO          ← nombre todo MAYÚSCULAS
        Cargo             ← cargo
        Area      ← área
        Organismo...

    Variante C — sello de confirmación GDE sin firmante humano:
        Digitally signed by GDE
        DN: ...
        Date: 2019.07.16 15:22:25 -03'00'
        [fin del texto o siguiente "Digitally signed by"]
    """
    firmantes = []
    bloques = re.split(r"(?=Digitally signed by)", texto, flags=re.IGNORECASE)

    for bloque in bloques:
        if not re.search(r"Digitally signed by", bloque, re.IGNORECASE):
            continue

        f = Firmante()

        m_nombre = _RE_SIGN_START.search(bloque)
        if m_nombre:
            f.nombre = m_nombre.group(1).strip()

        tiene_dn = bool(re.search(r"\bDN\s*:", bloque, re.IGNORECASE))

        # Sello GDE sin DN: puede ser un duplicado vacío (sello de confirmación)
        # o el único bloque de firma (APN sin DN). Se busca firmante post-Date:
        # si lo hay se extrae; si no, se descarta como sello sin datos útiles.
        if not tiene_dn and _es_sello_sistema(f.nombre):
            m_date_pos_nd = re.search(r"Date:[^\n]*\n", bloque, re.IGNORECASE)
            if not m_date_pos_nd:
                continue
            humano_nd = _extraer_bloque_humano(bloque[m_date_pos_nd.end():])
            if not humano_nd:
                continue
            f.nombre = humano_nd["nombre"]
            f.cargo  = humano_nd["cargo"]
            f.area   = humano_nd["area"]

        elif tiene_dn:
            # Normalizar DN en una sola línea (el PDF puede partir valores en varias líneas)
            dn_match = re.search(r"DN\s*:([\s\S]+?)(?=\nDate:|\Z)", bloque, re.IGNORECASE)
            dn_str = " ".join(dn_match.group(1).split()) if dn_match else ""

            m_ou = _RE_OU.findall(dn_str)
            if m_ou:
                f.cargo = m_ou[0].strip()

            m_o = re.search(
                r"(?<![a-z])o\s*=\s*([^,]+?)(?=\s*,\s*(?:ou|c|cn|sn)\s*=|$)",
                dn_str, re.IGNORECASE,
            )
            if m_o and not re.match(r"^(AR|C|CO)$", m_o.group(1).strip(), re.IGNORECASE):
                f.area = m_o.group(1).strip()

            # Variante B: buscar firmante humano en las líneas después de la Date
            # Variante C: si no hay firmante humano, es solo un sello de confirmación
            #             del sistema GDE → no agregar como firmante individual
            m_date_pos = re.search(r"Date:[^\n]*\n", bloque, re.IGNORECASE)
            humano = None
            if m_date_pos:
                post_date = bloque[m_date_pos.end():]
                humano = _extraer_bloque_humano(post_date)

            if humano and not _es_sello_sistema(humano["nombre"]):
                # Firmante humano real (AFIP Variante B): usar su identidad
                f.nombre = humano["nombre"]
                f.cargo  = humano["cargo"]
                f.area   = humano["area"]
            elif humano:
                # Sello de organismo externo detectado como "humano":
                # conservar nombre y cargo/área ya extraídos del DN; no sobreescribir
                pass
            else:
                # humano es None: nada después de Date
                # Sello de confirmación propio de GDE 
                # → omitir; el firmante humano ya fue o será capturado en otro bloque
                # Sello de organismo externo ("GESTION DOCUMENTAL ELECTRONICA - GDE",
                # etc.) → el sello en sí es el único firmante; conservar con datos del DN
                nombre_up = f.nombre.upper().strip()
                if nombre_up.startswith("GDE ") or nombre_up == "GDE":
                    continue
        else:
            # Variante A: cargo/área en líneas después de "Location:"
            m_loc = re.search(r"Location:[^\n]*\n([\s\S]+)", bloque, re.IGNORECASE)
            if m_loc:
                lineas = [l.strip() for l in m_loc.group(1).splitlines() if l.strip()]
                if len(lineas) >= 2:
                    f.cargo = lineas[1]
                if len(lineas) >= 3:
                    f.area = lineas[2]

            m_cuil_inline = re.search(
                r"(?:CUIL|CUIT)\s*[:\-]?\s*(\d{2}[-.]?\d{8}[-.]?\d)",
                bloque, re.IGNORECASE,
            )
            if m_cuil_inline:
                f.cuit = m_cuil_inline.group(1).strip()

        m_date = _RE_SIGN_DATE.search(bloque)
        if m_date:
            f.fecha_firma = m_date.group(1).strip()

        if f.nombre:
            firmantes.append(f)

    return _deduplicar_firmantes(firmantes)


def _extraer_bloque_humano(texto_post_date: str) -> "Optional[dict]":
    """
    Detecta si el texto inmediatamente después de 'Date:' corresponde
    a un firmante humano GDE con formato APELLIDO, NOMBRE (todo mayúsculas).

    Patrón esperado:
        APELLIDO, NOMBRE     ← todo mayúsculas, con coma o espacios
        Cargo
        Área
        Organismo
    """
    lineas = []
    for linea in texto_post_date.splitlines():
        s = linea.strip()
        if not s:
            continue
        if re.match(r"Digitally signed by", s, re.IGNORECASE):
            break
        lineas.append(s)
        if len(lineas) == 4:
            break

    if not lineas:
        return None

    primera = lineas[0]

    # Detectar prefijo "E/E" en la misma línea que el nombre 
    # E/E = En Ejercicio; se mueve al campo cargo, no al nombre
    ee_prefix = ""
    m_ee = re.match(r"^(E/E)\s+(.+)$", primera, re.IGNORECASE)
    if m_ee:
        ee_prefix = m_ee.group(1)
        primera = m_ee.group(2).strip()

    # El nombre GDE: predominantemente mayúsculas (el encoding del PDF puede
    # generar minúsculas puntuales, p. ej. 'i' por 'Í', 'a' por 'Á').
    # Se verifica longitud, que empiece con letra, que tenga separador y
    # que los caracteres fuera del juego esperado no superen 3 (tolerancia
    # para apóstrofes como D'ERRICO y artefactos de codificación como SEBASTI?N).
    primera_norm = primera.upper()
    if not (6 <= len(primera_norm) <= 60):
        return None
    if not primera_norm[0].isalpha():
        return None
    if sum(1 for c in primera_norm if c not in _CHARS_NOMBRE_FIRMANTE) > 3:
        return None
    if not re.search(r'[,\s]', primera):
        return None  # Una sola palabra → no es un nombre completo
    letras = [c for c in primera if c.isalpha()]
    if letras and sum(1 for c in letras if c.isupper()) / len(letras) < 0.6:
        return None  # Texto mixto (ej. "Jefe de Sección") → no es un nombre GDE

    cargo = lineas[1] if len(lineas) > 1 else ""
    if ee_prefix:
        cargo = f"{ee_prefix} {cargo}" if cargo else ee_prefix

    return {
        "nombre": primera.title(),
        "cargo": cargo,
        "area":  lineas[2] if len(lineas) > 2 else "",
    }


def _deduplicar_firmantes(firmantes: List[Firmante]) -> List[Firmante]:
    """
    Elimina entradas duplicadas dentro del mismo documento.
    Considera duplicado: mismo nombre (case-insensitive) + mismo cuit.
    Preserva el orden original (primera ocurrencia).
    """
    vistos: set = set()
    resultado = []
    for f in firmantes:
        clave = (f.nombre.lower().strip(), f.cuit.strip())
        if clave not in vistos:
            vistos.add(clave)
            resultado.append(f)
    return resultado


def _buscar_firmas_espanol(texto: str) -> List[Firmante]:
    """Fallback: busca patrones de firma en español."""
    firmantes = []
    for m in _RE_FIRMADO_ES.finditer(texto):
        f = Firmante(
            nombre=m.group(1).strip() if m.group(1) else "",
            cuit=m.group(2).strip() if m.group(2) else "",
            cargo=m.group(3).strip() if m.group(3) else "",
            area=m.group(4).strip() if m.group(4) else "",
        )
        if f.nombre:
            firmantes.append(f)
    return firmantes


def _extraer_destinatarios(texto: str) -> List[Destinatario]:
    """Extrae destinatarios de documentos ME/NO."""
    destinatarios = []
    lineas = texto.splitlines()
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        m_label = _RE_DEST_LABEL.match(linea)
        if not m_label:
            i += 1
            continue

        tipo_raw = m_label.group(1).strip().upper()
        tipo_norm = "A" if tipo_raw == "A" else "COPIA A"

        # Recoger el bloque completo incluyendo líneas de continuación
        bloque = m_label.group(2).strip()
        i += 1
        while i < len(lineas):
            siguiente = lineas[i].strip()
            if not siguiente or _RE_DEST_TERMINATOR.match(siguiente):
                break
            bloque += " " + siguiente
            i += 1

        # Extraer destinatarios individuales: "APELLIDO, NOMBRE (AREA)"
        for m in _RE_DEST_INDIVIDUO.finditer(bloque):
            nombre = m.group(1).strip().rstrip(",").strip()
            area = m.group(2).strip()
            if nombre:
                destinatarios.append(Destinatario(tipo=tipo_norm, nombre=nombre, area=area))

    return destinatarios
