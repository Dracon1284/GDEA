# GDEA — Procesador de Expedientes Electrónicos GDE

Programa de escritorio portable para Windows que procesa expedientes electrónicos del sistema **GDE (Gestión Documental Electrónica Argentina)**. A partir de un archivo ZIP descargado del GDE genera automáticamente un conjunto de reportes analíticos.

Funciona completamente de forma **local**: no requiere conexión a internet ni acceso a servidores externos.

---

## Características principales

- Extrae y analiza todos los PDFs de un expediente GDE
- Reconoce tipos de documentos: IF, ME, NO, PV, DI, SC y otros
- Detecta y extrae firmas digitales (nombre, cargo, área, fecha de firma)
- Extrae archivos embebidos dentro de los PDFs
- Genera 8 reportes configurables (activables/desactivables individualmente)
- Acepta expedientes `EX-*`, `Documentos-Ex-*` y ZIPs genéricos con solo PDFs
- Interfaz de terminal con menú interactivo

---

## Reportes generados

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `caratula.txt` | Texto del PV carátula + totales + timestamp |
| 2 | `indice.csv` | Un registro por documento con metadatos y último firmante |
| 3 | `firmantes.csv` | Un registro por firmante digital de cada documento |
| 4 | `destinatarios.csv` | Destinatarios de documentos ME y NO |
| 5 | `listado_embebidos.csv` | Listado de archivos embebidos con tamaño |
| 6 | `embebidos/` | Archivos embebidos extraídos, organizados por número de orden |
| 7 | `consolidado.pdf` | Todos los documentos fusionados en un único PDF |
| 8 | `consolidado_txt.txt` | Texto completo del expediente en formato plano |

---

## Requisitos

- **Windows 10 u 11**
- El ejecutable compilado (`GDEA.exe`) **no requiere Python ni ningún software adicional**

Para compilar desde el código fuente:
- Python 3.8 o superior
- Dependencias listadas en `requirements.txt`

---

## Uso

### Ejecutable (recomendado)

1. Descargar o compilar la carpeta `dist/GDEA/`
2. Hacer doble clic en `GDEA.exe`

### Desde el código fuente

```bat
:: Primera vez
setup.bat

:: Ejecuciones siguientes
run.bat
```

### Compilar el ejecutable

```bat
compilar.bat
```

El ejecutable queda en `dist\GDEA\GDEA.exe`.

---

## Estructura del proyecto

```
Proyecto5_GDEA/
├── main.py                  # Punto de entrada
├── gdea/
│   ├── config.py            # Configuración y definición de reportes
│   ├── menu.py              # Interfaz de menú (Rich)
│   ├── core/
│   │   ├── models.py        # Modelos de datos (Documento, Firmante, etc.)
│   │   ├── pdf_analyzer.py  # Análisis de PDFs GDE
│   │   └── zip_handler.py   # Manejo y validación de ZIPs
│   └── reports/
│       ├── caratula.py
│       ├── indice.py
│       ├── firmantes.py
│       ├── destinatarios.py
│       ├── listado_embebidos.py
│       ├── embebidos.py
│       ├── consolidado.py
│       └── consolidado_txt.py
├── GDEA.spec                # Configuración PyInstaller
├── compilar.bat             # Script de compilación
├── setup.bat / run.bat      # Scripts de ejecución en desarrollo
├── requirements.txt
├── icon.ico
├── LICENSE
└── Manual de uso.txt
```

---

## Licencia

MIT License — ver [LICENSE](LICENSE)

Copyright (c) 2026 Damian Patricio Soto
