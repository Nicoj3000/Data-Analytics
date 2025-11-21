# Scripts Adviser - Reacreditación Institucional

Sistema de análisis de datos para el proceso de reacreditación institucional de la Universidad Libre - Seccional Pereira.

## Descripción

Este proyecto contiene scripts de Python para analizar:
- Cargos directivos de egresados
- Estudiantes de posgrado y su relación con títulos previos de la universidad
- Análisis por programas y años de grado

## Protección de Datos

**IMPORTANTE:** La carpeta `data/` ha sido excluida del repositorio por motivos de protección de datos personales y confidencialidad institucional. Esta carpeta contiene:

- Información personal de egresados (nombres, cédulas, etc.)
- Bases de datos históricas de la universidad
- Encuestas con datos sensibles

**No se debe compartir ni subir esta carpeta a repositorios públicos o privados.**

## Estructura del Proyecto

```
├── app.py                          # Análisis de cargos directivos
├── egresados_posgrados.py         # Análisis de egresados en posgrados
├── egresados_posgrados_limpios.py # Análisis con CSV limpios
├── limpiar_csv_posgrados.py       # Script para limpiar CSVs
├── programas.py                    # Análisis por programas y años
├── totalxano.py                    # Análisis de todos los egresados
├── data/                           # (EXCLUIDA) Carpeta con datos sensibles
├── output/                         # Carpeta con resultados generados
└── .venv/                          # Entorno virtual de Python
```

## Requisitos

- Python 3.8+
- pandas
- openpyxl

## Instalación

1. Crear entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # En macOS/Linux
```

2. Instalar dependencias:
```bash
pip install pandas openpyxl
```

## Uso

Ejecutar cualquiera de los scripts según el análisis requerido:

```bash
python app.py                          # Análisis de cargos directivos
python limpiar_csv_posgrados.py       # Limpiar archivos CSV
python egresados_posgrados_limpios.py # Análisis de egresados
```

## Resultados

Los resultados se generan en la carpeta `output/` con archivos en formato CSV y Excel.

## Confidencialidad

Este proyecto maneja información confidencial de la Universidad Libre. Todo el personal que tenga acceso debe:
- Mantener la confidencialidad de los datos
- No compartir información personal de egresados
- Seguir las políticas de protección de datos de la institución

---

**Universidad Libre - Seccional Pereira**
*Proceso de Reacreditación Institucional 2025*
