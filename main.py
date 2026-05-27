#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GDEA — Procesador de Expedientes Electrónicos GDE
Punto de entrada principal.
"""
import sys
import os

# Windows: forzar UTF-8 en la consola antes de cargar Rich
# (necesario cuando se ejecuta el .exe compilado sin chcp 65001 previo)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Asegurar que el directorio del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rich.console import Console
    console = Console()
except ImportError:
    print("ERROR: Las dependencias no están instaladas.")
    print("Ejecute setup.bat (Windows) o bash setup.sh (Linux/Mac) primero.")
    input("Presione Enter para salir...")
    sys.exit(1)

try:
    import fitz
except ImportError:
    console.print(
        "[bold red]ERROR:[/bold red] PyMuPDF no está instalado.\n"
        "Ejecute [bold]setup.bat[/bold] para instalar las dependencias."
    )
    input("Presione Enter para salir...")
    sys.exit(1)


def main():
    from gdea.menu import GDEAMenu
    app = GDEAMenu()
    try:
        app.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrumpido por el usuario.[/dim]")
    except Exception as e:
        console.print(f"\n[bold red]Error inesperado:[/bold red] {e}")
        console.print_exception()
        input("Presione Enter para salir...")
        sys.exit(1)


if __name__ == "__main__":
    main()
