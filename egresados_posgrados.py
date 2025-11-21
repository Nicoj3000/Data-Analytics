#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para identificar estudiantes de posgrado que son egresados de Universidad Libre
Compara las cédulas de estudiantes de posgrado (2021-2025) con la base de datos histórica
de egresados desde 1974.
"""

import pandas as pd
import os
from pathlib import Path

def cargar_base_datos_egresados(ruta_bdd):
    """
    Carga la base de datos histórica de egresados y extrae las cédulas únicas.
    """
    print("\n📚 Cargando base de datos histórica de egresados...")
    
    # Intentar diferentes encodings
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            df = pd.read_csv(ruta_bdd, sep=';', encoding=encoding, dtype=str)
            break
        except:
            continue
    
    # Buscar la columna de identificación
    columna_cedula = None
    for col in df.columns:
        col_upper = col.upper().strip()
        if 'IDENTIFICACI' in col_upper or 'CEDULA' in col_upper or 'DOCUMENTO' in col_upper:
            columna_cedula = col
            break
    
    if not columna_cedula:
        print("❌ No se encontró la columna de identificación en la BDD")
        return set()
    
    # Extraer cédulas únicas, limpiando valores vacíos
    cedulas = set()
    for cedula in df[columna_cedula].dropna().unique():
        cedula_limpia = str(cedula).strip()
        if cedula_limpia and cedula_limpia != '' and cedula_limpia.lower() != 'nan':
            cedulas.add(cedula_limpia)
    
    print(f"✓ Total de egresados históricos identificados: {len(cedulas):,}")
    return cedulas

def extraer_codigo_programa(nombre_programa):
    """
    Extrae el código del programa (primeros 5 dígitos).
    Ejemplo: "32101    ESPECIALIZACION EN DERECHO ADMINISTRATIVO" -> "32101"
    """
    if pd.isna(nombre_programa):
        return None
    
    nombre_str = str(nombre_programa).strip()
    # Buscar los primeros dígitos
    partes = nombre_str.split()
    if partes and partes[0].isdigit():
        return partes[0]
    return None

def extraer_nombre_programa_limpio(nombre_programa):
    """
    Extrae el nombre del programa eliminando información de resoluciones y pensum.
    Solo mantiene el código y nombre del programa.
    """
    if pd.isna(nombre_programa):
        return None
    
    nombre_str = str(nombre_programa).strip()
    
    # Si contiene RESOLUCION o RESOLUCIÓN, cortar hasta ese punto
    if 'RESOLUCION' in nombre_str.upper() or 'RESOLUCIÓN' in nombre_str.upper():
        # Encontrar donde comienza RESOLUCION
        idx_res = -1
        for variante in ['RESOLUCION', 'RESOLUCIÓN', 'Resolucion', 'Resolución']:
            if variante in nombre_str:
                idx_res = nombre_str.find(variante)
                break
        
        if idx_res > 0:
            # Extraer solo hasta antes de RESOLUCION
            nombre_limpio = nombre_str[:idx_res].strip()
            # Remover espacios extras al final
            return nombre_limpio.rstrip()
    
    # Si no tiene RESOLUCION, devolver tal cual
    return nombre_str

def procesar_archivo_posgrados(ruta_archivo, cedulas_egresados, año):
    """
    Procesa un archivo de posgrados y cuenta cuántos estudiantes son egresados de ULibre.
    Lee línea por línea para capturar la estructura compleja con múltiples secciones.
    """
    print(f"\n📄 Procesando archivo: {os.path.basename(ruta_archivo)}")
    
    # Cargar archivo con diferentes encodings
    df = None
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            df = pd.read_csv(ruta_archivo, sep=';', encoding=encoding, dtype=str, header=None)
            break
        except:
            continue
    
    if df is None:
        print("❌ No se pudo leer el archivo")
        return []
    
    programa_actual = None
    resultados = []
    estudiantes_vistos = set()  # Para evitar duplicados
    
    # Recorrer todas las filas
    for idx, row in df.iterrows():
        # Convertir la fila a string para análisis
        fila_str = ' '.join([str(val) for val in row if pd.notna(val)]).strip()
        
        # Detectar líneas de programa (comienzan con código de 5 dígitos)
        primera_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        segunda_col = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
        
        # Identificar programa - puede estar en primera o segunda columna
        if primera_col and len(primera_col) >= 5 and primera_col[:5].isdigit():
            programa_actual = primera_col
            continue
        elif segunda_col and len(segunda_col) >= 5 and segunda_col[:5].isdigit():
            programa_actual = segunda_col
            continue
        
        # También buscar en toda la fila si contiene un código de programa
        for val in row:
            if pd.notna(val):
                val_str = str(val).strip()
                # Buscar patrón de código de programa (5 dígitos seguidos de nombre de programa)
                # PERO ignorar líneas que son solo resoluciones/pensum
                if (len(val_str) > 20 and val_str[:5].isdigit() and 
                    any(palabra in val_str.upper() for palabra in ['ESPECIALIZACION', 'MAESTRIA', 'DOCTORADO']) and
                    'RESOLUCION' not in val_str.upper() and 'PENSUM' not in val_str.upper()):
                    programa_actual = val_str
                    break
        
        # Buscar filas que contienen "Nombre" e "Identificación" como encabezados
        if 'Nombre' in fila_str and 'Identificaci' in fila_str:
            continue
        
        # Ignorar filas que son solo información de resoluciones o pensum
        if primera_col and ('Pensum' in primera_col or 'RESOLUCION' in primera_col.upper()):
            continue
        
        # Buscar columnas de datos de estudiantes
        # La estructura típica es: ;NOMBRE;;;;;;CEDULA;;CODIGO;GRUPO;...
        # Buscar en todas las columnas el nombre y la cédula
        nombre_encontrado = None
        cedula_encontrada = None
        codigo_encontrado = None
        
        for col_idx, valor in enumerate(row):
            if pd.notna(valor):
                valor_str = str(valor).strip()
                
                # Si el valor parece un nombre (contiene letras y espacios, más de 5 caracteres)
                if (len(valor_str) > 5 and 
                    any(c.isalpha() for c in valor_str) and 
                    ' ' in valor_str and
                    'UNIVERSIDAD' not in valor_str.upper() and
                    'Nombre' not in valor_str and
                    'Nivel' not in valor_str and
                    'Pensum' not in valor_str and
                    'Programa' not in valor_str and
                    'Periodo' not in valor_str and
                    'Facultad' not in valor_str):
                    nombre_encontrado = valor_str
                
                # Si el valor parece una cédula o código (solo dígitos, entre 6 y 12 caracteres)
                # La cédula viene ANTES del código en el CSV, así que guardamos la primera
                if (valor_str.isdigit() and 
                    6 <= len(valor_str) <= 12 and
                    valor_str != '20211' and valor_str != '20221' and  # No es periodo
                    valor_str != '20231' and valor_str != '20241' and
                    valor_str != '20251'):
                    # Si ya tenemos una cédula, este es el código
                    if cedula_encontrada is None:
                        cedula_encontrada = valor_str
                    elif codigo_encontrado is None:
                        codigo_encontrado = valor_str
        
        # Si encontramos nombre y cédula en la misma fila, es un estudiante
        if nombre_encontrado and cedula_encontrada:
            # Evitar duplicados
            clave_unica = f"{cedula_encontrada}_{programa_actual}"
            if clave_unica not in estudiantes_vistos:
                estudiantes_vistos.add(clave_unica)
                
                es_egresado = cedula_encontrada in cedulas_egresados
                
                resultados.append({
                    'Año': año,
                    'Programa_Codigo': extraer_codigo_programa(programa_actual) if programa_actual else 'Sin_Codigo',
                    'Programa_Nombre': extraer_nombre_programa_limpio(programa_actual) if programa_actual else 'Sin_Programa',
                    'Nombre': nombre_encontrado,
                    'Identificacion': cedula_encontrada,
                    'Es_Egresado_ULibre': 'Sí' if es_egresado else 'No'
                })
    
    print(f"  ✓ Estudiantes procesados: {len(resultados)}")
    if len(resultados) > 0:
        egresados_count = sum(1 for r in resultados if r['Es_Egresado_ULibre'] == 'Sí')
        print(f"  ✓ Egresados de ULibre identificados: {egresados_count} ({egresados_count/len(resultados)*100:.1f}%)")
    
    return resultados

def generar_reportes(df_completo, carpeta_salida):
    """
    Genera reportes por año y programa, organizando por año con archivos separados.
    """
    print("\n📊 Generando reportes...")
    
    # Asegurar que la carpeta de salida existe
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)
    
    # 1. Reporte completo con todos los estudiantes
    archivo_completo = os.path.join(carpeta_salida, 'estudiantes_posgrados_completo.csv')
    df_completo.to_csv(archivo_completo, index=False, encoding='utf-8-sig', sep=';')
    print(f"✓ Archivo completo guardado: {archivo_completo}")
    
    # 2. Generar archivo CSV por cada año
    for año in sorted(df_completo['Año'].unique()):
        df_año = df_completo[df_completo['Año'] == año].copy()
        
        # Crear resumen por programa para este año
        # IMPORTANTE: Agrupar SOLO por código (no por nombre completo con resolución)
        resumen_año = df_año.groupby(['Programa_Codigo']).agg({
            'Programa_Nombre': 'first',  # Tomar el primer nombre (ya limpio)
            'Identificacion': 'count',
            'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
        }).reset_index()
        
        resumen_año.columns = ['Codigo_Programa', 'Nombre_Programa', 'Total_Estudiantes', 'Egresados_ULibre']
        resumen_año['Porcentaje'] = (
            resumen_año['Egresados_ULibre'] / resumen_año['Total_Estudiantes'] * 100
        ).round(2)
        
        # Ordenar por código de programa
        resumen_año = resumen_año.sort_values('Codigo_Programa')
        
        # Guardar CSV por año
        archivo_año_csv = os.path.join(carpeta_salida, f'egresados_posgrados_{int(año)}.csv')
        resumen_año.to_csv(archivo_año_csv, index=False, encoding='utf-8-sig', sep=';')
        print(f"✓ Archivo {int(año)} guardado: {archivo_año_csv}")
    
    # 3. Resumen consolidado todos los años
    # Agrupar solo por año y código (no por nombre con resolución)
    resumen_programa_año = df_completo.groupby(['Año', 'Programa_Codigo']).agg({
        'Programa_Nombre': 'first',
        'Identificacion': 'count',
        'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
    }).reset_index()
    
    resumen_programa_año.columns = ['Año', 'Codigo_Programa', 'Nombre_Programa', 'Total_Estudiantes', 'Egresados_ULibre']
    resumen_programa_año['Porcentaje'] = (
        resumen_programa_año['Egresados_ULibre'] / resumen_programa_año['Total_Estudiantes'] * 100
    ).round(2)
    
    archivo_consolidado = os.path.join(carpeta_salida, 'consolidado_todos_los_años.csv')
    resumen_programa_año.to_csv(archivo_consolidado, index=False, encoding='utf-8-sig', sep=';')
    print(f"✓ Consolidado guardado: {archivo_consolidado}")
    
    # 4. Resumen general por año
    resumen_año_general = df_completo.groupby('Año').agg({
        'Identificacion': 'count',
        'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
    }).reset_index()
    
    resumen_año_general.columns = ['Año', 'Total_Estudiantes', 'Egresados_ULibre']
    resumen_año_general['Porcentaje'] = (
        resumen_año_general['Egresados_ULibre'] / resumen_año_general['Total_Estudiantes'] * 100
    ).round(2)
    
    archivo_resumen = os.path.join(carpeta_salida, 'resumen_general_por_año.csv')
    resumen_año_general.to_csv(archivo_resumen, index=False, encoding='utf-8-sig', sep=';')
    print(f"✓ Resumen general guardado: {archivo_resumen}")
    
    # 5. Excel con múltiples hojas (una por año)
    archivo_excel = os.path.join(carpeta_salida, 'egresados_posgrados_por_año.xlsx')
    with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
        # Hoja de resumen general
        resumen_año_general.to_excel(writer, sheet_name='Resumen General', index=False)
        
        # Una hoja por año con detalle de programas
        for año in sorted(df_completo['Año'].unique()):
            df_año = df_completo[df_completo['Año'] == año]
            # Agrupar solo por código
            resumen_año_detalle = df_año.groupby(['Programa_Codigo']).agg({
                'Programa_Nombre': 'first',
                'Identificacion': 'count',
                'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
            }).reset_index()
            resumen_año_detalle.columns = ['Codigo', 'Programa', 'Total', 'Egresados_ULibre']
            resumen_año_detalle['Porcentaje'] = (
                resumen_año_detalle['Egresados_ULibre'] / resumen_año_detalle['Total'] * 100
            ).round(2)
            resumen_año_detalle = resumen_año_detalle.sort_values('Codigo')
            
            resumen_año_detalle.to_excel(writer, sheet_name=f'{int(año)}', index=False)
    
    print(f"✓ Excel por año guardado: {archivo_excel}")
    
    # Mostrar estadísticas detalladas
    print("\n" + "="*80)
    print("📈 RESUMEN POR AÑO Y PROGRAMA")
    print("="*80)
    
    for año in sorted(df_completo['Año'].unique()):
        df_año = df_completo[df_completo['Año'] == año]
        total_año = len(df_año)
        egresados_año = (df_año['Es_Egresado_ULibre'] == 'Sí').sum()
        
        print(f"\n{'='*80}")
        print(f"📅 AÑO {int(año)}")
        print(f"{'='*80}")
        print(f"Total estudiantes: {total_año:,} | Egresados ULibre: {egresados_año:,} ({egresados_año/total_año*100:.1f}%)")
        print(f"\n{'Programa':<60} {'Total':>8} {'Egresados':>10} {'%':>6}")
        print("-" * 80)
        
        # Agrupar solo por código de programa
        resumen_programas = df_año.groupby('Programa_Codigo').agg({
            'Programa_Nombre': 'first',
            'Identificacion': 'count',
            'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
        }).reset_index().sort_values('Programa_Codigo')
        
        for _, row in resumen_programas.iterrows():
            programa = row['Programa_Nombre'][:55] if len(row['Programa_Nombre']) > 55 else row['Programa_Nombre']
            total = int(row['Identificacion'])
            egresados = int(row['Es_Egresado_ULibre'])
            porcentaje = egresados / total * 100 if total > 0 else 0
            print(f"{programa:<60} {total:>8} {egresados:>10} {porcentaje:>6.1f}%")

def main():
    # Rutas de archivos
    directorio_base = os.path.dirname(os.path.abspath(__file__))
    carpeta_datos = os.path.join(directorio_base, 'data', 'posgrados')
    carpeta_salida = os.path.join(directorio_base, 'output', 'egresados-posgrados')
    
    ruta_bdd = os.path.join(carpeta_datos, 'BDD. 1974 ACTUALIZADA CON GRADOS DEL 14 DE NOVIEMBRE 2025 (1).csv')
    
    print("="*60)
    print("🎓 ANÁLISIS DE EGRESADOS EN PROGRAMAS DE POSGRADO")
    print("="*60)
    
    # 1. Cargar base de datos de egresados
    cedulas_egresados = cargar_base_datos_egresados(ruta_bdd)
    
    if not cedulas_egresados:
        print("❌ Error: No se pudo cargar la base de datos de egresados")
        return
    
    # 2. Procesar cada archivo de posgrados
    todos_resultados = []
    
    for año in range(2021, 2026):
        archivo = os.path.join(carpeta_datos, f'{año}-Posgrados.csv')
        
        if os.path.exists(archivo):
            resultados = procesar_archivo_posgrados(archivo, cedulas_egresados, año)
            todos_resultados.extend(resultados)
        else:
            print(f"⚠️  Archivo no encontrado: {archivo}")
    
    # 3. Crear DataFrame completo
    if todos_resultados:
        df_completo = pd.DataFrame(todos_resultados)
        
        # 4. Generar reportes
        generar_reportes(df_completo, carpeta_salida)
        
        print("\n✅ Análisis completado exitosamente")
    else:
        print("\n❌ No se procesaron datos")

if __name__ == "__main__":
    main()
