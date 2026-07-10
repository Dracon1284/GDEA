# GDEA — Procesador de Expedientes Electrónicos GDE

Programa de escritorio portable para Windows que procesa expedientes electrónicos del sistema **GDE (Gestión Documental Electrónica Argentina)**. A partir de un archivo ZIP descargado del GDE genera automáticamente un conjunto de reportes analíticos.

Funciona completamente de forma **local**: no requiere conexión a internet ni acceso a servidores externos.

---

## Características principales

- Extrae y analiza todos los PDFs de un expediente GDE
- Reconoce tipos de documentos: IF, ME, NO, PV, DI, SC y otros
- Detecta y extrae firmas digitales (nombre, cargo, área, fecha de firma)
- Extrae archivos embebidos dentro de los PDFs
- Genera 10 reportes configurables (activables/desactivables individualmente)
- Acepta expedientes `EX-*`, `Documentos-Ex-*` y ZIPs genéricos con solo PDFs
- Interfaz de terminal con menú interactivo

---

## Reportes generados

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `reporte.xlsx` | Resumen, índice, firmantes, destinatarios y embebidos en hojas de un Excel |
| 2 | `caratula_y_orden.txt` | PV carátula + resumen estadístico + verificación de orden cronológico |
| 3 | `indice.csv` | Un registro por documento con metadatos y último firmante |
| 4 | `firmantes.csv` | Un registro por firmante digital de cada documento |
| 5 | `destinatarios.csv` | Destinatarios de documentos ME y NO |
| 6 | `listado_embebidos.csv` | Listado de archivos embebidos con tamaño |
| 7 | `embebidos/` | Archivos embebidos extraídos, organizados por número de orden |
| 8 | `consolidado.pdf` | Todos los documentos fusionados en un único PDF (con OCR) |
| 9 | `consolidado.txt` | Texto completo del expediente en formato plano |
| 10 | `documentos/` | PDFs individuales del expediente extraídos del ZIP |

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
│       ├── excel.py
│       ├── caratula_y_orden.py
│       ├── indice.py
│       ├── firmantes.py
│       ├── destinatarios.py
│       ├── listado_embebidos.py
│       ├── embebidos.py
│       ├── consolidado.py
│       ├── consolidado_txt.py
│       └── log.py
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
