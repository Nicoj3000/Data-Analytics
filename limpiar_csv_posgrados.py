#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpiar y normalizar los archivos CSV de posgrados (2021-2025)
Genera archivos CSV limpios con formato tabular simple
"""

import pandas as pd
import os
from pathlib import Path


def extraer_codigo_programa(texto):
    """Extrae el código de programa de 5 dígitos"""
    if pd.isna(texto):
        return None
    
    texto_str = str(texto).strip()
    
    # Buscar patrón de 5 dígitos
    palabras = texto_str.split()
    for palabra in palabras:
        if palabra.isdigit() and len(palabra) == 5:
            return palabra
    
    return None


def limpiar_nombre_programa(texto):
    """Limpia el nombre del programa removiendo metadata de resolución"""
    if pd.isna(texto):
        return ""
    
    texto_str = str(texto).strip()
    
    # Remover el código de 5 dígitos del inicio
    palabras = texto_str.split(maxsplit=1)
    if len(palabras) > 1 and palabras[0].isdigit() and len(palabras[0]) == 5:
        texto_str = palabras[1]
    
    # Remover metadata de RESOLUCION
    for variante in ['RESOLUCION', 'RESOLUCIÓN', 'Resolucion', 'Resolución']:
        if variante in texto_str.upper():
            idx = texto_str.upper().find(variante.upper())
            if idx > 0:
                texto_str = texto_str[:idx].strip()
                break
    
    return texto_str.strip()


def procesar_archivo_posgrados(archivo_path, año):
    """Procesa un archivo CSV de posgrados y retorna lista de registros limpios"""
    print(f"\n{'='*80}")
    print(f"Procesando: {archivo_path.name} - Año {año}")
    print(f"{'='*80}")
    
    # Leer archivo sin headers
    try:
        df = pd.read_csv(archivo_path, sep=';', header=None, dtype=str, encoding='utf-8')
    except:
        df = pd.read_csv(archivo_path, sep=';', header=None, dtype=str, encoding='latin-1')
    
    registros = []
    facultad_actual = ""
    programa_codigo = ""
    programa_nombre = ""
    
    for idx, row in df.iterrows():
        # Convertir toda la fila a string
        row = row.fillna('')
        primera_col = str(row[0]).strip()
        segunda_col = str(row[1]).strip() if len(row) > 1 else ''
        
        # Detectar Facultad
        if primera_col == 'Facultad':
            facultad_actual = segunda_col
            continue
        
        # Detectar Programa
        if primera_col == 'Programa':
            programa_codigo = extraer_codigo_programa(segunda_col)
            programa_nombre = limpiar_nombre_programa(segunda_col)
            continue
        
        # Ignorar líneas administrativas
        if primera_col in ['Pensum', 'Nivel', 'Nombre', '']:
            continue
        
        if 'RESOLUCION' in primera_col.upper() or 'RESOLUCIÓN' in primera_col.upper():
            continue
        
        # Detectar estudiantes
        nombre_estudiante = primera_col
        
        # Validar que sea un nombre de estudiante válido
        if len(nombre_estudiante) <= 5:
            continue
        
        if not any(c.isalpha() for c in nombre_estudiante):
            continue
        
        if nombre_estudiante.upper() in ['NIVEL', 'NOMBRE', 'FACULTAD', 'PROGRAMA', 'PENSUM']:
            continue
        
        # Extraer cedula y codigo (primeros dos valores numéricos de 6-12 dígitos)
        cedula_encontrada = None
        codigo_encontrado = None
        grupo_encontrado = None
        
        for col_idx, valor in enumerate(row):
            valor_str = str(valor).strip()
            
            # Buscar valores numéricos
            if valor_str.isdigit() and 6 <= len(valor_str) <= 12:
                # Primer valor = cedula, segundo = codigo
                if cedula_encontrada is None:
                    cedula_encontrada = valor_str
                elif codigo_encontrado is None:
                    codigo_encontrado = valor_str
            
            # Buscar grupo (números pequeños de 1-3 dígitos, no en notación científica)
            if valor_str.isdigit() and 1 <= len(valor_str) <= 3:
                grupo_encontrado = valor_str
        
        # Validar cedula
        if not cedula_encontrada or len(cedula_encontrada) < 6:
            continue
        
        # Crear registro limpio
        registro = {
            'Año': año,
            'Facultad': facultad_actual,
            'Codigo_Programa': programa_codigo or '',
            'Nombre_Programa': programa_nombre or '',
            'Nombre_Estudiante': nombre_estudiante,
            'Cedula': cedula_encontrada,
            'Codigo_Estudiante': codigo_encontrado or '',
            'Grupo': grupo_encontrado or ''
        }
        
        registros.append(registro)
    
    print(f"Total estudiantes procesados: {len(registros)}")
    
    # Mostrar resumen por programa
    if registros:
        df_registros = pd.DataFrame(registros)
        resumen = df_registros.groupby(['Codigo_Programa', 'Nombre_Programa']).size().reset_index(name='Total')
        print("\nResumen por programa:")
        for _, row in resumen.iterrows():
            print(f"  {row['Codigo_Programa']} - {row['Nombre_Programa']}: {row['Total']} estudiantes")
    
    return registros


def main():
    """Función principal"""
    print("\n" + "="*80)
    print("SCRIPT PARA LIMPIAR ARCHIVOS CSV DE POSGRADOS")
    print("="*80)
    
    # Directorios
    dir_base = Path(__file__).parent
    dir_entrada = dir_base / 'data' / 'posgrados'
    dir_salida = dir_base / 'data' / 'posgrados_limpios'
    
    # Crear directorio de salida
    dir_salida.mkdir(parents=True, exist_ok=True)
    
    # Archivos a procesar
    archivos = [
        ('2021-Posgrados.csv', 2021),
        ('2022-Posgrados.csv', 2022),
        ('2023-Posgrados.csv', 2023),
        ('2024-Posgrados.csv', 2024),
        ('2025-Posgrados.csv', 2025)
    ]
    
    todos_registros = []
    
    # Procesar cada archivo
    for nombre_archivo, año in archivos:
        archivo_path = dir_entrada / nombre_archivo
        
        if not archivo_path.exists():
            print(f"⚠️  Archivo no encontrado: {archivo_path}")
            continue
        
        registros = procesar_archivo_posgrados(archivo_path, año)
        todos_registros.extend(registros)
        
        # Guardar archivo individual limpio
        if registros:
            df_limpio = pd.DataFrame(registros)
            archivo_salida = dir_salida / f"{año}-Posgrados-limpio.csv"
            df_limpio.to_csv(archivo_salida, index=False, encoding='utf-8-sig', sep=';')
            print(f"✅ Archivo limpio guardado: {archivo_salida}")
    
    # Guardar archivo consolidado
    if todos_registros:
        print(f"\n{'='*80}")
        print("GENERANDO ARCHIVO CONSOLIDADO")
        print(f"{'='*80}")
        
        df_consolidado = pd.DataFrame(todos_registros)
        archivo_consolidado = dir_salida / 'Todos-los-años-consolidado.csv'
        df_consolidado.to_csv(archivo_consolidado, index=False, encoding='utf-8-sig', sep=';')
        
        print(f"\n✅ Archivo consolidado guardado: {archivo_consolidado}")
        print(f"   Total registros: {len(todos_registros)}")
        
        # Resumen general
        print("\n" + "="*80)
        print("RESUMEN GENERAL")
        print("="*80)
        
        resumen_años = df_consolidado.groupby('Año').size().reset_index(name='Total_Estudiantes')
        print("\nEstudiantes por año:")
        for _, row in resumen_años.iterrows():
            print(f"  {row['Año']}: {row['Total_Estudiantes']} estudiantes")
        
        resumen_programas = df_consolidado.groupby(['Codigo_Programa', 'Nombre_Programa']).size().reset_index(name='Total')
        resumen_programas = resumen_programas.sort_values('Total', ascending=False)
        print(f"\nTotal de programas únicos: {len(resumen_programas)}")
        print("\nTop 10 programas con más estudiantes (todos los años):")
        for idx, row in resumen_programas.head(10).iterrows():
            print(f"  {row['Codigo_Programa']} - {row['Nombre_Programa']}: {row['Total']} estudiantes")
    
    print(f"\n{'='*80}")
    print("PROCESO COMPLETADO")
    print(f"{'='*80}")
    print(f"\nArchivos limpios guardados en: {dir_salida}")


if __name__ == "__main__":
    main()
