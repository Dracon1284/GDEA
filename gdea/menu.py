# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Damian Patricio Soto
"""
Menú principal de GDEA con interfaz de terminal usando Rich.
"""
import re
import sys
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt
from rich import box

from .config import (
    REPORTES, REPORTES_VISIBLES, OPCIONES, MODOS, VERSION,
    cargar_config, guardar_config, verificar_marker,
    resolver_reportes, hay_reportes_activos,
)
from .core.zip_handler import (
    validar_zip, extraer_zip, obtener_pdfs,
    clasificar_zip, pdfs_tienen_prefijo_orden, obtener_pdfs_sin_orden,
)
from .core.pdf_analyzer import analizar_pdf, es_caratula_expediente

console = Console()


def _cls():
    """Limpia la pantalla de forma compatible con todas las consolas de Windows."""
    import os
    os.system('cls')


def _nombre_carpeta_expediente(zip_path: str) -> str:
    """
    Devuelve el nombre de la subcarpeta de salida según el tipo de ZIP:
      · EX-*           →  'EX-XXXXXXXXXXXXX'
      · Documentos-Ex-* →  'EX-XXXXXXXXXXXXX'  (extrae el número desde el prefijo)
      · Genérico        →  'Reportes (stem del ZIP)'
    """
    stem = Path(zip_path).stem
    tipo = clasificar_zip(zip_path)

    if tipo == "EX":
        return "EX-" + stem[3:16]

    if tipo == "DOC_EX":
        # "Documentos-Ex-" tiene 14 caracteres (case-insensitive)
        m = re.match(r'[Dd]ocumentos[-_][Ee][Xx][-_](.*)', stem)
        if m:
            return "EX-" + m.group(1)[:13]
        # Fallback: quitar los primeros 14 chars
        return "EX-" + stem[14:27]

    # GENERICO
    return f"Reportes - {stem}"


def _confirmar(pregunta: str, default: bool = True) -> bool:
    """Prompt de confirmación localizado con s/n en lugar de y/n."""
    while True:
        respuesta = Prompt.ask(f"{pregunta} (s/n)").strip().lower()
        if not respuesta:
            return default
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        console.print("  [yellow]Responda 's' o 'n'.[/yellow]")


def _dialogo_abrir_zip() -> "str | None":
    """
    Abre el diálogo nativo de Windows para elegir un archivo ZIP.
    Devuelve la ruta seleccionada, o None si se cancela o falla.
    """
    if sys.platform != "win32":
        return None

    import ctypes
    from ctypes import wintypes

    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ("lStructSize", wintypes.DWORD),
            ("hwndOwner", wintypes.HWND),
            ("hInstance", wintypes.HINSTANCE),
            ("lpstrFilter", wintypes.LPCWSTR),
            ("lpstrCustomFilter", wintypes.LPWSTR),
            ("nMaxCustFilter", wintypes.DWORD),
            ("nFilterIndex", wintypes.DWORD),
            ("lpstrFile", wintypes.LPWSTR),
            ("nMaxFile", wintypes.DWORD),
            ("lpstrFileTitle", wintypes.LPWSTR),
            ("nMaxFileTitle", wintypes.DWORD),
            ("lpstrInitialDir", wintypes.LPCWSTR),
            ("lpstrTitle", wintypes.LPCWSTR),
            ("Flags", wintypes.DWORD),
            ("nFileOffset", wintypes.WORD),
            ("nFileExtension", wintypes.WORD),
            ("lpstrDefExt", wintypes.LPCWSTR),
            ("lCustData", wintypes.LPARAM),
            ("lpfnHook", ctypes.c_void_p),
            ("lpTemplateName", wintypes.LPCWSTR),
            ("pvReserved", ctypes.c_void_p),
            ("dwReserved", wintypes.DWORD),
            ("FlagsEx", wintypes.DWORD),
        ]

    OFN_FILEMUSTEXIST = 0x00001000
    OFN_PATHMUSTEXIST = 0x00000800
    OFN_HIDEREADONLY = 0x00000004
    OFN_NOCHANGEDIR = 0x00000008
    OFN_EXPLORER = 0x00080000

    def _multi_sz(partes):
        s = "\0".join(partes) + "\0\0"
        buf = (ctypes.c_wchar * len(s))()
        for i, ch in enumerate(s):
            buf[i] = ch
        return buf

    filtro = _multi_sz([
        "Archivos ZIP (*.zip)", "*.zip",
        "Todos los archivos (*.*)", "*.*",
    ])
    buffer = ctypes.create_unicode_buffer(32768)
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    ofn.hwndOwner = hwnd
    ofn.lpstrFilter = ctypes.cast(filtro, wintypes.LPCWSTR)
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
    ofn.nMaxFile = len(buffer)
    ofn.lpstrTitle = "Seleccione el archivo ZIP del expediente"
    ofn.Flags = (
        OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_HIDEREADONLY
        | OFN_NOCHANGEDIR | OFN_EXPLORER
    )
    ofn.lpstrDefExt = "zip"

    GetOpenFileNameW = ctypes.windll.comdlg32.GetOpenFileNameW
    GetOpenFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
    GetOpenFileNameW.restype = wintypes.BOOL

    ok = bool(GetOpenFileNameW(ctypes.byref(ofn)))
    if hwnd:
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    if not ok:
        return None
    ruta = buffer.value.strip().strip('"')
    return ruta or None

BANNER = """
 ██████╗ ██████╗ ███████╗ █████╗
██╔════╝ ██╔══██╗██╔════╝██╔══██╗
██║  ███╗██║  ██║█████╗  ███████║
██║   ██║██║  ██║██╔══╝  ██╔══██║
╚██████╔╝██████╔╝███████╗██║  ██║
 ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
"""


class GDEAMenu:
    def __init__(self):
        self.config = cargar_config()

    def run(self):
        while True:
            opcion = self._mostrar_menu_principal()
            if opcion == "1":
                self._flujo_procesamiento()
            elif opcion == "2":
                self._flujo_procesamiento_rapido()
            elif opcion == "3":
                self._menu_opciones()
            elif opcion == "4":
                self._acerca_de()
            elif opcion == "0":
                console.print("\n[bold cyan]Hasta luego.[/bold cyan]\n")
                break

    # ─── Menú principal ───────────────────────────────────────────────────────

    def _mostrar_menu_principal(self) -> str:
        _cls()
        console.print(Text(BANNER, style="bold cyan"), justify="center")
        console.print(
            Panel(
                "[bold white]Procesador de Expedientes Electrónicos GDE - V.1.4[/bold white]",
                style="cyan",
                padding=(0, 2),
            )
        )

        # Tabla de reportes activos
        tabla = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        tabla.add_column("", style="dim", width=3)
        tabla.add_column("Reporte", style="white")
        tabla.add_column("Estado", style="dim")

        for key, info in REPORTES.items():
            estado = "[green]+ Activo[/green]" if self.config.get(key) else ""
            tabla.add_row("-", info["nombre"], estado)

        console.print(tabla)
        console.print()

        console.print("  [bold cyan]\\[1][/bold cyan] Iniciar procesamiento")
        console.print("  [bold cyan]\\[2][/bold cyan] Procesamiento rápido")
        console.print("  [bold cyan]\\[3][/bold cyan] Opciones (activar/desactivar reportes)")
        console.print("  [bold cyan]\\[4][/bold cyan] Acerca de")
        console.print("  [bold cyan]\\[0][/bold cyan] Salir")
        console.print()

        while True:
            valor = Prompt.ask(
                "  Seleccione una opción [bold cyan]\\[1/2/3/4/0][/bold cyan]",
                choices=["1", "2", "3", "4", "0"],
                show_choices=False,
            )
            return valor

    # ─── Menú de opciones ─────────────────────────────────────────────────────

    def _sincronizar_reportes(self):
        flags = resolver_reportes(self.config.get("modo", "A"), self.config.get("opciones", {}))
        self.config.update(flags)

    def _menu_opciones(self):
        mensaje = ""
        while True:
            self._sincronizar_reportes()
            _cls()
            console.print(
                Panel("[bold white]Opciones — Reportes a generar[/bold white]", style="cyan")
            )

            console.print("[bold]Reportes[/bold]")
            tabla_r = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            tabla_r.add_column("", width=12)
            tabla_r.add_column("Reporte", style="white", min_width=38)
            tabla_r.add_column("Descripción", style="dim", max_width=58, overflow="fold")
            for key in REPORTES_VISIBLES:
                info = REPORTES[key]
                estado = "[green]+ Activo[/green]" if self.config.get(key) else "[red]- Inactivo[/red]"
                tabla_r.add_row(estado, info["nombre"], info["descripcion"])
            console.print(tabla_r)
            console.print()

            console.print("[bold]Opciones[/bold]")
            tabla_o = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            tabla_o.add_column("N°", style="bold yellow", width=4)
            tabla_o.add_column("Opción", style="white", min_width=32)
            tabla_o.add_column("Descripción", style="dim", max_width=52, overflow="fold")
            tabla_o.add_column("Estado", width=14)
            ops = self.config.setdefault("opciones", {k: True for k in OPCIONES})
            for key, info in OPCIONES.items():
                activo = bool(ops.get(key, True))
                estado = "[green]+ Activo[/green]" if activo else "[red]- Inactivo[/red]"
                tabla_o.add_row(info["numero"], info["nombre"], info["descripcion"], estado)
            console.print(tabla_o)
            console.print()

            console.print("[bold]Modo[/bold]")
            tabla_m = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            tabla_m.add_column("N°", style="bold yellow", width=4)
            tabla_m.add_column("Modo", style="white", min_width=22)
            tabla_m.add_column("Descripción", style="dim", max_width=58, overflow="fold")
            tabla_m.add_column("Estado", width=18)
            modo_actual = str(self.config.get("modo", "A")).upper()
            for letra, info in MODOS.items():
                sel = letra == modo_actual
                estado = (
                    "[green]+ Seleccionado[/green]" if sel else "[red]- No Seleccionado[/red]"
                )
                tabla_m.add_row(letra, info["nombre"], info["descripcion"], estado)
            console.print(tabla_m)
            console.print()

            console.print("  Ingrese el número de la opción para activar/desactivar.")
            console.print("  [bold white]\\[0][/bold white] Volver al menú principal")
            console.print()
            if mensaje:
                console.print(f"  [yellow]{mensaje}[/yellow]")
                mensaje = ""

            valor = Prompt.ask("  Activar/Desactivar/Selección Modo").strip()
            if valor == "0":
                break

            comando = valor.upper()
            if comando in OPCIONES or comando in {info["numero"] for info in OPCIONES.values()}:
                clave = comando if comando in OPCIONES else None
                if clave is None:
                    for k, info in OPCIONES.items():
                        if info["numero"] == comando:
                            clave = k
                            break
                if clave:
                    ops[clave] = not bool(ops.get(clave, True))
                    self.config["opciones"] = ops
                    continue

            if comando in MODOS:
                self.config["modo"] = comando
                continue

            mensaje = "Opción no válida. Use 1-4, A-C o 0."

        self._sincronizar_reportes()
        guardar_config(self.config)

    # ─── Acerca de ───────────────────────────────────────────────────────────

    def _acerca_de(self):
        _cls()
        console.print(Text(BANNER, style="bold cyan"), justify="center")
        console.print(
            Panel("[bold white]Acerca de GDEA[/bold white]", style="cyan")
        )

        tabla = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        tabla.add_column("", style="dim", width=14)
        tabla.add_column("", style="white")
        tabla.add_row("Programa:", "GDEA — Procesador de Expedientes Electrónicos GDE")
        tabla.add_row("Versión:",  VERSION)
        tabla.add_row("Autor:",    "Damian Patricio Soto")
        tabla.add_row("Año:",      "2026")
        tabla.add_row("Licencia:", "MIT License")
        console.print(tabla)

        console.print()
        console.print(
            Panel(
                "Copyright (c) 2026 Damian Patricio Soto\n\n"
                "Se otorga permiso, de forma gratuita, a cualquier persona que obtenga\n"
                "una copia de este software y de los archivos de documentación asociados\n"
                "(el \"Software\"), para utilizar el Software sin restricción, incluyendo\n"
                "sin limitación los derechos de usar, copiar, modificar, fusionar,\n"
                "publicar, distribuir, sublicenciar y/o vender copias del Software, y\n"
                "permitir a las personas a quienes se les proporcione el Software hacer\n"
                "lo mismo, sujeto a las siguientes condiciones:\n\n"
                "El aviso de copyright anterior y este aviso de permiso deberán incluirse\n"
                "en todas las copias o partes sustanciales del Software.\n\n"
                "EL SOFTWARE SE PROPORCIONA \"TAL CUAL\", SIN GARANTÍA DE NINGÚN TIPO,\n"
                "EXPRESA O IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A LAS GARANTÍAS DE\n"
                "COMERCIABILIDAD, IDONEIDAD PARA UN PROPÓSITO PARTICULAR Y NO INFRACCIÓN.\n"
                "EN NINGÚN CASO LOS AUTORES O TITULARES DEL COPYRIGHT SERÁN RESPONSABLES\n"
                "DE NINGUNA RECLAMACIÓN, DAÑO U OTRA RESPONSABILIDAD.",
                title="[bold white]Licencia MIT[/bold white]",
                style="dim",
                padding=(1, 2),
            )
        )

        console.print()
        console.print("  [bold white]\\[0][/bold white] Volver al menú principal")
        console.print()
        Prompt.ask("  Opción", choices=["0"])

    # ─── Flujo de procesamiento ───────────────────────────────────────────────

    def _aviso_sin_reportes(self) -> bool:
        """True si no hay reportes activos (y ya se informó al usuario)."""
        if hay_reportes_activos(self.config):
            return False
        console.print()
        console.print(
            Panel(
                "[yellow]No hay ningún reporte activo.[/yellow]\n"
                "Active al menos un reporte en el menú de Opciones antes de procesar.",
                title="[bold yellow]Sin reportes[/bold yellow]",
                style="yellow",
            )
        )
        console.print()
        Prompt.ask("  Presione Enter para continuar")
        return True

    def _flujo_procesamiento(self, aviso: str = ""):
        _cls()
        console.print(Panel("[bold white]Iniciar procesamiento[/bold white]", style="cyan"))
        if aviso:
            console.print()
            console.print(f"  [yellow]{aviso}[/yellow]")

        if self._aviso_sin_reportes():
            return

        zip_path = self._pedir_zip()
        if zip_path is None:
            return

        base_dir = self._pedir_carpeta_salida(zip_path)
        if base_dir is None:
            return

        self._confirmar_y_procesar(zip_path, base_dir)

    def _flujo_procesamiento_rapido(self):
        _cls()
        console.print(Panel("[bold white]Procesamiento rápido[/bold white]", style="cyan"))

        if self._aviso_sin_reportes():
            return

        console.print()
        console.print("  [dim]Seleccione el archivo ZIP en la ventana de Windows...[/dim]")
        zip_path = _dialogo_abrir_zip()

        if not zip_path:
            self._flujo_procesamiento(
                aviso="No se seleccionó un archivo ZIP. Se continúa con Iniciar procesamiento."
            )
            return

        valido, error = validar_zip(zip_path)
        if not valido:
            self._flujo_procesamiento(
                aviso=f"{error} Se continúa con Iniciar procesamiento."
            )
            return

        base_dir = str(Path(zip_path).resolve().parent)
        console.print(f"  [green]+[/green] Archivo válido: [cyan]{Path(zip_path).name}[/cyan]")
        console.print(
            "  [dim]La carpeta de reportes se creará en la misma ruta del archivo ZIP.[/dim]"
        )
        console.print(f"  [green]+[/green] Carpeta base: [cyan]{base_dir}[/cyan]")
        self._confirmar_y_procesar(zip_path, base_dir, misma_ruta_zip=True)

    def _confirmar_y_procesar(self, zip_path: str, base_dir: str, misma_ruta_zip: bool = False):
        tipo_zip = clasificar_zip(zip_path)
        carpeta_exp = _nombre_carpeta_expediente(zip_path)
        output_dir = str(Path(base_dir) / carpeta_exp)
        console.print(f"  [green]+[/green] Subcarpeta de salida: [cyan]{carpeta_exp}[/cyan]")

        ya_procesado, info = verificar_marker(output_dir)
        if ya_procesado:
            console.print()
            console.print(
                Panel(
                    f"[yellow]Esta carpeta ya fue procesada anteriormente:[/yellow]\n{info}",
                    title="[bold yellow]Advertencia[/bold yellow]",
                    style="yellow",
                )
            )
            if not _confirmar("  ¿Desea sobreescribir los reportes existentes?", default=False):
                return

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        console.print()
        self._mostrar_resumen_previo(zip_path, output_dir, misma_ruta_zip=misma_ruta_zip)
        console.print()

        if not _confirmar("  ¿Desea continuar?", default=True):
            return

        self._procesar(zip_path, output_dir, tipo_zip)

    def _pedir_zip(self) -> "str | None":
        console.print()
        console.print("  [dim]Ingrese la ruta al archivo ZIP o la carpeta que lo contiene.[/dim]")
        console.print("  [dim]Ejemplo: C:\\Expedientes\\EX- ... .zip[/dim]")
        console.print("  [dim]         C:\\Expedientes[/dim]")
        console.print("  [dim]Se aceptan: archivos EX-*, Documentos-Ex-* y ZIPs que contengan solo PDFs.[/dim]")
        console.print()
        console.print("  [bold white]\\[0][/bold white] Volver al menú principal")
        console.print()

        while True:
            valor = Prompt.ask("  Ruta al archivo ZIP").strip()
            if not valor or valor == "0":
                return None

            # Limpiar comillas que pueda pegar el usuario desde el explorador
            valor = valor.strip('"').strip("'")
            path = Path(valor)

            # Si es carpeta, listar los ZIPs disponibles para seleccionar
            if path.is_dir():
                zips = sorted(path.glob("*.zip"), key=lambda z: z.name.lower())
                if not zips:
                    console.print(
                        "  [yellow]No se encontraron archivos ZIP en esa carpeta.[/yellow]"
                    )
                    continue

                console.print()
                console.print("  [bold]Archivos ZIP encontrados:[/bold]")
                for i, z in enumerate(zips, 1):
                    console.print(f"    [bold white]\\[{i}][/bold white] {z.name}")
                console.print("    [bold white]\\[0][/bold white] Volver")
                console.print()

                seleccion = None
                while True:
                    sel = Prompt.ask("  Seleccione un archivo").strip()
                    if sel == "0":
                        break
                    try:
                        idx = int(sel) - 1
                        if 0 <= idx < len(zips):
                            seleccion = str(zips[idx])
                            break
                        console.print("  [yellow]Número fuera de rango.[/yellow]")
                    except ValueError:
                        console.print("  [yellow]Ingrese un número válido.[/yellow]")

                if seleccion is None:
                    continue
                valor = seleccion

            valido, error = validar_zip(valor)
            if valido:
                console.print(f"  [green]+[/green] Archivo válido: [cyan]{Path(valor).name}[/cyan]")
                return valor
            else:
                console.print(f"  [red]-[/red] {error}")

    def _pedir_carpeta_salida(self, zip_path: str) -> "str | None":
        console.print()
        console.print("  [dim]Ingrese la ruta de la carpeta base donde se guardarán los reportes.[/dim]")
        console.print("  [dim]Presione Enter sin valor para volver.[/dim]")
        console.print()

        while True:
            valor = Prompt.ask("  Carpeta de salida").strip().strip('"').strip("'")
            if not valor:
                return None

            output_path = Path(valor)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                console.print(f"  [green]+[/green] Carpeta base: [cyan]{valor}[/cyan]")
                return valor
            except Exception as e:
                console.print(f"  [red]-[/red] No se pudo acceder a la carpeta: {e}")

    def _mostrar_resumen_previo(self, zip_path: str, output_dir: str, misma_ruta_zip: bool = False):
        tabla = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        tabla.add_column("", style="dim")
        tabla.add_column("", style="white")
        tabla.add_row("ZIP:", Path(zip_path).name)
        tabla.add_row("Salida:", output_dir)
        if misma_ruta_zip:
            tabla.add_row(
                "Nota:",
                "La carpeta de reportes se crea en la misma ruta del archivo ZIP",
            )
        tabla.add_row(
            "Reportes:",
            ", ".join(
                REPORTES[k]["nombre"].split(" (")[0]
                for k in REPORTES
                if self.config.get(k)
            ) or "[red]Ninguno seleccionado[/red]",
        )
        console.print(tabla)

    # ─── Motor de procesamiento ───────────────────────────────────────────────

    def _procesar(self, zip_path: str, output_dir: str, tipo: str = "EX"):
        from .reports.excel import generar_excel
        from .reports.caratula_y_orden import generar_caratula_y_orden
        from .reports.indice import generar_indice
        from .reports.firmantes import generar_firmantes
        from .reports.destinatarios import generar_destinatarios
        from .reports.listado_embebidos import generar_listado_embebidos
        from .reports.consolidado import generar_consolidado
        from .reports.consolidado_txt import generar_consolidado_txt
        from .reports.embebidos import extraer_todos_embebidos

        inicio = datetime.now()
        console.print()

        # ── Paso 1: Extraer ZIP ────────────────────────────────────────────────
        with console.status("[cyan]Extrayendo ZIP...[/cyan]"):
            try:
                carpeta_docs = extraer_zip(zip_path, output_dir)
                pdfs = obtener_pdfs(carpeta_docs)
            except Exception as e:
                console.print(f"[bold red]Error al extraer el ZIP:[/bold red] {e}")
                return

        console.print(f"  [green]+[/green] ZIP extraído — [bold]{len(pdfs)}[/bold] documentos encontrados")

        if not pdfs:
            console.print("[yellow]No se encontraron archivos PDF en el ZIP.[/yellow]")
            return

        # Para ZIPs genéricos: verificar si los PDFs tienen prefijo de orden
        orden_asignado = False
        if tipo == "GENERICO" and not pdfs_tienen_prefijo_orden(pdfs):
            pdfs = obtener_pdfs_sin_orden(carpeta_docs)
            orden_asignado = True
            console.print(
                "  [dim]  PDFs sin prefijo de orden — se asignará orden alfabético.[/dim]"
            )

        # ── Paso 2: Analizar PDFs ─────────────────────────────────────────────
        documentos = []
        errores = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}[/cyan]"),
            BarColumn(),
            TextColumn("[white]{task.completed}/{task.total}[/white]"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            tarea = progress.add_task("Analizando documentos...", total=len(pdfs))

            for i, pdf_path in enumerate(pdfs, 1):
                nombre = Path(pdf_path).name
                progress.update(tarea, description=f"Analizando: {nombre[:50]}")
                orden_override = f"{i:04d}" if orden_asignado else None
                doc = analizar_pdf(pdf_path, numero_orden_override=orden_override)
                documentos.append(doc)
                if doc.error:
                    errores.append(f"{nombre}: {doc.error}")
                progress.advance(tarea)

        console.print(f"  [green]+[/green] Análisis completado")
        if errores:
            console.print(f"  [yellow]!!![/yellow]  {len(errores)} documentos con advertencias")

        # Identificar carátula
        caratula_doc = None
        for doc in documentos:
            if doc.tipo == "PV":
                if es_caratula_expediente(doc, doc.texto_completo) or caratula_doc is None:
                    caratula_doc = doc
                    if es_caratula_expediente(doc, doc.texto_completo):
                        break

        # ── Paso 3: Generar reportes ──────────────────────────────────────────
        resultados = {}

        # (1) Reporte Excel
        if self.config.get("excel"):
            with console.status("[cyan]Generando Reporte Excel...[/cyan]"):
                try:
                    ruta = generar_excel(caratula_doc, documentos, output_dir)
                    resultados["excel"] = ruta
                except Exception as e:
                    console.print(f"  [red]-[/red]  Reporte Excel: {e}")

        # (2) Carátula y orden
        if self.config.get("caratula_y_orden"):
            with console.status("[cyan]Generando carátula y orden TXT...[/cyan]"):
                try:
                    if caratula_doc:
                        ruta = generar_caratula_y_orden(caratula_doc, caratula_doc.texto_completo, documentos, output_dir)
                        resultados["caratula_y_orden"] = ruta
                    else:
                        resultados["caratula_y_orden"] = None
                        console.print("  [yellow]!!![/yellow]  No se encontró documento PV carátula")
                except Exception as e:
                    console.print(f"  [red]-[/red]  Carátula: {e}")

        # (3) Índice
        if self.config.get("indice"):
            with console.status("[cyan]Generando índice CSV...[/cyan]"):
                try:
                    ruta = generar_indice(documentos, output_dir)
                    resultados["indice"] = ruta
                except Exception as e:
                    console.print(f"  [red]-[/red]  Índice: {e}")

        # (4) Firmantes
        if self.config.get("firmantes"):
            with console.status("[cyan]Generando registro de firmantes CSV...[/cyan]"):
                try:
                    ruta = generar_firmantes(documentos, output_dir)
                    resultados["firmantes"] = ruta
                except Exception as e:
                    console.print(f"  [red]-[/red]  Firmantes: {e}")

        # (5) Destinatarios
        if self.config.get("destinatarios"):
            with console.status("[cyan]Generando destinatarios CSV...[/cyan]"):
                try:
                    ruta = generar_destinatarios(documentos, output_dir)
                    resultados["destinatarios"] = ruta
                except Exception as e:
                    console.print(f"  [red]-[/red]  Destinatarios: {e}")

        # (6) Listado de embebidos
        if self.config.get("listado_embebidos"):
            with console.status("[cyan]Generando listado de archivos embebidos CSV...[/cyan]"):
                try:
                    ruta = generar_listado_embebidos(documentos, output_dir)
                    resultados["listado_embebidos"] = ruta
                except Exception as e:
                    console.print(f"  [red]-[/red]  Listado embebidos: {e}")

        # (7) Extracción de embebidos
        if self.config.get("embebidos"):
            with console.status("[cyan]Extrayendo archivos embebidos...[/cyan]"):
                try:
                    ruta = extraer_todos_embebidos(documentos, output_dir)
                    resultados["embebidos"] = ruta
                except Exception as e:
                    console.print(f"  [red]-[/red]  Embebidos: {e}")

        # (8) y (9) Consolidados
        # Seccionar: se pregunta una sola vez para ambos reportes consolidados
        total = len(documentos)
        seccionar = False
        if (self.config.get("consolidado") or self.config.get("consolidado_txt")) and total > 100:
            console.print()
            console.print(
                f"  [yellow]El expediente tiene [bold]{total}[/bold] documentos (más de 100).[/yellow]"
            )
            seccionar = _confirmar(
                "  ¿Desea seccionar los reportes consolidados cada 100 documentos?",
                default=True,
            )

        if self.config.get("consolidado"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}[/cyan]"),
                BarColumn(),
                TextColumn("[white]{task.completed}/{task.total}[/white]"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                tarea_pdf = progress.add_task("Generando PDF consolidado...", total=total)

                def avanzar(n=1):
                    progress.advance(tarea_pdf, n)

                try:
                    rutas = generar_consolidado(documentos, output_dir, seccionar, callback=avanzar)
                    resultados["consolidado"] = rutas
                except Exception as e:
                    console.print(f"  [red]-[/red]  Consolidado: {e}")

        if self.config.get("consolidado_txt"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}[/cyan]"),
                BarColumn(),
                TextColumn("[white]{task.completed}/{task.total}[/white]"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                tarea_txt = progress.add_task("Generando TXT consolidado...", total=total)

                def avanzar_txt(n=1):
                    progress.advance(tarea_txt, n)

                try:
                    rutas = generar_consolidado_txt(documentos, output_dir, seccionar, callback=avanzar_txt)
                    resultados["consolidado_txt"] = rutas
                except Exception as e:
                    console.print(f"  [red]-[/red]  Consolidado TXT: {e}")

        # (10) Extracción de documentos: si está desactivado, se elimina la carpeta
        #      'Documentos' (se extrae siempre porque el análisis la necesita).
        if self.config.get("extraer_documentos"):
            resultados["extraer_documentos"] = carpeta_docs
        else:
            try:
                shutil.rmtree(carpeta_docs, ignore_errors=True)
            except Exception as e:
                console.print(f"  [red]-[/red]  No se pudo eliminar la carpeta Documentos: {e}")

        # ── Paso 4: Generar log (marcador de procesamiento) ───────────────────
        from .reports.log import generar_log
        duracion = (datetime.now() - inicio).total_seconds()
        try:
            ruta_log = generar_log(zip_path, documentos, output_dir, VERSION, duracion)
            resultados["log"] = ruta_log
        except Exception as e:
            console.print(f"  [red]-[/red]  Log: {e}")

        # ── Resumen final ─────────────────────────────────────────────────────
        self._mostrar_resumen_final(documentos, resultados, errores, output_dir, duracion)

    # ─── Resumen final ────────────────────────────────────────────────────────

    def _mostrar_resumen_final(self, documentos, resultados, errores, output_dir, duracion):
        console.print()
        console.print(
            Panel(
                "[bold green]Procesamiento completado[/bold green]",
                style="green",
            )
        )

        tabla = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        tabla.add_column("", style="dim")
        tabla.add_column("", style="white")

        tabla.add_row("Documentos procesados:", str(len(documentos)))
        tabla.add_row(
            "Archivos embebidos totales:",
            str(sum(d.cantidad_embebidos for d in documentos)),
        )
        tabla.add_row("Tiempo:", f"{duracion:.1f} segundos")
        tabla.add_row("Carpeta de salida:", output_dir)
        console.print(tabla)

        if resultados:
            console.print()
            console.print("  [bold]Reportes generados:[/bold]")
            for nombre, ruta in resultados.items():
                if ruta:
                    if isinstance(ruta, list):
                        for r in ruta:
                            console.print(f"  [green]+[/green] {Path(r).name}")
                    else:
                        console.print(f"  [green]+[/green] {Path(str(ruta)).name}")

        if errores:
            console.print()
            console.print(f"  [yellow]Advertencias ({len(errores)}):[/yellow]")
            for e in errores[:5]:
                console.print(f"  [dim]  {e}[/dim]")
            if len(errores) > 5:
                console.print(f"  [dim]  ... y {len(errores) - 5} más[/dim]")

        console.print()
        Prompt.ask("  Presione Enter para continuar")
