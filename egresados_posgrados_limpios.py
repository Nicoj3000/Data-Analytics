#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para identificar estudiantes de posgrado que son egresados de Universidad Libre
de OTROS programas (diferentes al programa de posgrado actual).
Usa los archivos CSV limpios generados por limpiar_csv_posgrados.py
"""

import pandas as pd
import os
from pathlib import Path


def cargar_base_datos_egresados_detallada(ruta_bdd):
    """
    Carga la base de datos histórica de egresados con información del programa y fecha.
    Retorna un diccionario: {cedula: [(titulo, año_grado), ...]}
    """
    print("\n📚 Cargando base de datos histórica de egresados...")
    
    # Intentar diferentes encodings
    df = None
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            df = pd.read_csv(ruta_bdd, sep=';', encoding=encoding, dtype=str)
            break
        except:
            continue
    
    if df is None:
        print("❌ No se pudo leer el archivo de la BDD")
        return {}
    
    # Buscar columnas necesarias
    columna_cedula = None
    columna_titulo = None
    columna_fecha = None
    
    for col in df.columns:
        col_upper = col.upper().strip()
        if 'IDENTIFICACI' in col_upper or 'CEDULA' in col_upper or 'DOCUMENTO' in col_upper:
            columna_cedula = col
        if 'TITULO' in col_upper or 'PROGRAMA' in col_upper or 'CARRERA' in col_upper:
            if columna_titulo is None:  # Tomar la primera columna de título encontrada
                columna_titulo = col
        if 'FECHA' in col_upper and 'GRADO' in col_upper:
            columna_fecha = col
    
    if not columna_cedula or not columna_titulo:
        print(f"❌ No se encontraron las columnas necesarias")
        print(f"   Columna cédula: {columna_cedula}")
        print(f"   Columna título: {columna_titulo}")
        print(f"   Columna fecha: {columna_fecha}")
        return {}
    
    print(f"✓ Usando columnas: '{columna_cedula}', '{columna_titulo}' y '{columna_fecha}'")
    
    # Crear diccionario: cedula -> lista de (titulo, año_grado)
    egresados_detalle = {}
    
    for idx, row in df.iterrows():
        cedula = str(row[columna_cedula]).strip()
        titulo = str(row[columna_titulo]).strip().upper()
        
        # Validar cedula y titulo
        if not cedula or cedula == '' or cedula.lower() == 'nan':
            continue
        if not titulo or titulo == '' or titulo.lower() == 'nan' or titulo == 'NAN':
            continue
        
        # Extraer año de la fecha de grado
        año_grado = None
        if columna_fecha and columna_fecha in row:
            fecha_str = str(row[columna_fecha]).strip()
            try:
                # Intentar extraer año de diferentes formatos: DD/MM/YYYY, YYYY-MM-DD, etc.
                if '/' in fecha_str:
                    partes = fecha_str.split('/')
                    if len(partes) == 3:
                        año_grado = int(partes[-1])  # Último elemento es el año
                elif '-' in fecha_str:
                    partes = fecha_str.split('-')
                    if len(partes) == 3:
                        año_grado = int(partes[0])  # Primer elemento es el año
            except:
                pass
        
        # Agregar al diccionario
        if cedula not in egresados_detalle:
            egresados_detalle[cedula] = []
        
        # Evitar duplicados
        registro = (titulo, año_grado)
        if registro not in egresados_detalle[cedula]:
            egresados_detalle[cedula].append(registro)
    
    print(f"✓ Total de egresados identificados: {len(egresados_detalle):,}")
    
    # Estadísticas de títulos múltiples
    con_multiples = sum(1 for titulos in egresados_detalle.values() if len(titulos) > 1)
    print(f"✓ Egresados con múltiples títulos: {con_multiples:,}")
    
    return egresados_detalle


def extraer_tipo_y_nombre_programa(codigo_programa, nombre_programa):
    """
    Extrae el tipo de programa (ESPECIALIZACION, MAESTRIA, etc.) y nombre base
    """
    nombre_upper = nombre_programa.upper().strip()
    
    # Determinar tipo de programa
    tipo = None
    if 'ESPECIALIZACION' in nombre_upper or codigo_programa.startswith('32'):
        tipo = 'ESPECIALIZACION'
    elif 'MAESTRIA' in nombre_upper or 'MAESTRÍA' in nombre_upper or codigo_programa.startswith('34'):
        tipo = 'MAESTRIA'
    elif 'DOCTORADO' in nombre_upper:
        tipo = 'DOCTORADO'
    
    return tipo, nombre_upper


def verificar_egresado_otro_programa(cedula, año_cursando, codigo_programa_actual, nombre_programa_actual, egresados_detalle):
    """
    Verifica si el estudiante es egresado de UN PROGRAMA DIFERENTE de ULibre,
    graduado ANTES del año en que está cursando el posgrado actual.
    
    Retorna:
    - (True, lista_programas_previos) si es egresado de otro(s) programa(s) anterior(es)
    - (False, []) si no es egresado o solo del mismo programa actual
    """
    if cedula not in egresados_detalle:
        return False, []
    
    titulos_con_fecha = egresados_detalle[cedula]  # [(titulo, año_grado), ...]
    
    # Obtener tipo y nombre del programa actual
    tipo_actual, nombre_actual = extraer_tipo_y_nombre_programa(codigo_programa_actual, nombre_programa_actual)
    
    # Buscar títulos DIFERENTES al programa actual Y con fecha ANTERIOR
    programas_diferentes = []
    
    for titulo, año_grado in titulos_con_fecha:
        titulo_upper = titulo.upper().strip()
        
        # Verificar si es el mismo programa
        es_mismo_programa = False
        
        # Comparar por nombre (ej: "ESPECIALIZACION EN DERECHO PENAL" vs "DERECHO PENAL")
        if tipo_actual and tipo_actual in titulo_upper:
            # Es del mismo tipo, verificar si es el mismo nombre
            # Extraer la parte del nombre después del tipo
            nombre_en_titulo = titulo_upper.replace(tipo_actual, '').replace('EN', '').strip()
            nombre_actual_limpio = nombre_actual.replace(tipo_actual, '').replace('EN', '').strip()
            
            # Si los nombres coinciden significativamente, es el mismo programa
            if nombre_en_titulo in nombre_actual_limpio or nombre_actual_limpio in nombre_en_titulo:
                es_mismo_programa = True
        
        # CRÍTICO: Verificar que la fecha de grado sea ANTERIOR al año cursando
        # Si no hay fecha de grado, asumir que podría ser posterior (excluir por seguridad)
        fecha_es_anterior = False
        if año_grado is not None:
            try:
                año_cursando_int = int(año_cursando)
                # El grado debe ser al menos 1 año antes de cursar el posgrado
                # (no puede graduarse y el mismo año estar "cursando")
                if año_grado < año_cursando_int:
                    fecha_es_anterior = True
            except:
                pass
        
        # Si NO es el mismo programa Y la fecha es anterior, agregarlo
        if not es_mismo_programa and fecha_es_anterior:
            programas_diferentes.append(f"{titulo} ({año_grado})")
    
    # Es egresado si tiene al menos un título diferente con fecha anterior
    es_egresado = len(programas_diferentes) > 0
    
    return es_egresado, programas_diferentes


def procesar_archivo_limpio(archivo_path, egresados_detalle):
    """
    Procesa un archivo CSV limpio de posgrados verificando títulos previos
    """
    print(f"\n{'='*80}")
    print(f"Procesando: {archivo_path.name}")
    print(f"{'='*80}")
    
    # Leer el archivo limpio
    df = pd.read_csv(archivo_path, sep=';', dtype=str, encoding='utf-8-sig')
    
    resultados = []
    
    for idx, row in df.iterrows():
        año = row['Año']
        cedula = str(row['Cedula']).strip()
        codigo_programa = str(row['Codigo_Programa']).strip()
        nombre_programa = str(row['Nombre_Programa']).strip()
        nombre_estudiante = str(row['Nombre_Estudiante']).strip()
        
        # Verificar si es egresado de OTRO programa CON FECHA ANTERIOR
        es_egresado, programas_previos = verificar_egresado_otro_programa(
            cedula, año, codigo_programa, nombre_programa, egresados_detalle
        )
        
        registro = {
            'Año': año,
            'Programa_Codigo': codigo_programa,
            'Programa_Nombre': nombre_programa,
            'Nombre': nombre_estudiante,
            'Identificacion': cedula,
            'Es_Egresado_ULibre': 'Sí' if es_egresado else 'No',
            'Programas_Previos': ' | '.join(programas_previos) if programas_previos else ''
        }
        
        resultados.append(registro)
    
    egresados_count = sum(1 for r in resultados if r['Es_Egresado_ULibre'] == 'Sí')
    print(f"Total estudiantes procesados: {len(resultados)}")
    print(f"Egresados de otros programas ULibre (con título anterior): {egresados_count}")
    
    return resultados


def generar_reportes(resultados, dir_salida):
    """
    Genera los reportes y archivos de salida
    """
    print(f"\n{'='*80}")
    print("GENERANDO REPORTES")
    print(f"{'='*80}")
    
    # Crear DataFrame con todos los resultados
    df_completo = pd.DataFrame(resultados)
    
    # Guardar base de datos completa
    archivo_completo = dir_salida / 'estudiantes_posgrados_completo.csv'
    df_completo.to_csv(archivo_completo, index=False, encoding='utf-8-sig', sep=';')
    print(f"\n✓ Base de datos completa guardada: {archivo_completo}")
    
    # Generar reportes por año
    años = sorted(df_completo['Año'].unique())
    
    for año in años:
        df_año = df_completo[df_completo['Año'] == año].copy()
        
        # Agrupar por código de programa
        resumen_año = df_año.groupby(['Programa_Codigo']).agg({
            'Programa_Nombre': 'first',
            'Identificacion': 'count',
            'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
        }).reset_index()
        
        resumen_año.columns = ['Codigo_Programa', 'Nombre_Programa', 'Total_Estudiantes', 'Egresados_ULibre']
        resumen_año['No_Egresados'] = resumen_año['Total_Estudiantes'] - resumen_año['Egresados_ULibre']
        resumen_año['Porcentaje'] = (resumen_año['Egresados_ULibre'] / resumen_año['Total_Estudiantes'] * 100).round(2)
        
        # Ordenar por código de programa
        resumen_año = resumen_año.sort_values('Codigo_Programa')
        
        # Guardar archivo CSV del año
        archivo_año = dir_salida / f'egresados_posgrados_{año}.csv'
        resumen_año.to_csv(archivo_año, index=False, encoding='utf-8-sig', sep=';')
        
        print(f"\n{'='*80}")
        print(f"AÑO {año}")
        print(f"{'='*80}")
        print(f"Total estudiantes: {len(df_año)}")
        print(f"Egresados ULibre (de otros programas): {(df_año['Es_Egresado_ULibre'] == 'Sí').sum()}")
        print(f"Solo estudiantes (sin título previo): {(df_año['Es_Egresado_ULibre'] == 'No').sum()}")
        print(f"Porcentaje egresados: {((df_año['Es_Egresado_ULibre'] == 'Sí').sum() / len(df_año) * 100):.2f}%")
        print(f"\nDetalle por programa:")
        for _, row in resumen_año.iterrows():
            print(f"  {row['Codigo_Programa']} - {row['Nombre_Programa']}")
            print(f"    Total: {row['Total_Estudiantes']} | Egresados: {row['Egresados_ULibre']} | Solo estudiantes: {row['No_Egresados']} | {row['Porcentaje']:.1f}%")
    
    # Generar archivo consolidado
    consolidado = []
    for año in años:
        df_año = df_completo[df_completo['Año'] == año].copy()
        resumen_año = df_año.groupby(['Programa_Codigo']).agg({
            'Programa_Nombre': 'first',
            'Identificacion': 'count',
            'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
        }).reset_index()
        
        resumen_año['Año'] = año
        resumen_año.columns = ['Codigo_Programa', 'Nombre_Programa', 'Total_Estudiantes', 'Egresados_ULibre', 'Año']
        resumen_año['Solo_Estudiantes'] = resumen_año['Total_Estudiantes'] - resumen_año['Egresados_ULibre']
        resumen_año['Porcentaje'] = (resumen_año['Egresados_ULibre'] / resumen_año['Total_Estudiantes'] * 100).round(2)
        resumen_año = resumen_año[['Año', 'Codigo_Programa', 'Nombre_Programa', 'Total_Estudiantes', 'Egresados_ULibre', 'Solo_Estudiantes', 'Porcentaje']]
        consolidado.append(resumen_año)
    
    df_consolidado = pd.concat(consolidado, ignore_index=True)
    archivo_consolidado = dir_salida / 'consolidado_todos_los_años.csv'
    df_consolidado.to_csv(archivo_consolidado, index=False, encoding='utf-8-sig', sep=';')
    print(f"\n✓ Archivo consolidado guardado: {archivo_consolidado}")
    
    # Generar resumen general por año
    resumen_general = []
    for año in años:
        df_año = df_completo[df_completo['Año'] == año]
        total = len(df_año)
        egresados = (df_año['Es_Egresado_ULibre'] == 'Sí').sum()
        porcentaje = (egresados / total * 100) if total > 0 else 0
        
        resumen_general.append({
            'Año': año,
            'Total_Estudiantes': total,
            'Egresados_ULibre': egresados,
            'Solo_Estudiantes': total - egresados,
            'Porcentaje_Egresados': round(porcentaje, 2)
        })
    
    df_resumen_general = pd.DataFrame(resumen_general)
    archivo_resumen = dir_salida / 'resumen_general_por_año.csv'
    df_resumen_general.to_csv(archivo_resumen, index=False, encoding='utf-8-sig', sep=';')
    print(f"✓ Resumen general guardado: {archivo_resumen}")
    
    # Generar archivo Excel con múltiples hojas
    archivo_excel = dir_salida / 'egresados_posgrados_por_año.xlsx'
    with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
        df_resumen_general.to_excel(writer, sheet_name='Resumen General', index=False)
        
        for año in años:
            df_año = df_completo[df_completo['Año'] == año].copy()
            resumen_año = df_año.groupby(['Programa_Codigo']).agg({
                'Programa_Nombre': 'first',
                'Identificacion': 'count',
                'Es_Egresado_ULibre': lambda x: (x == 'Sí').sum()
            }).reset_index()
            
            resumen_año.columns = ['Codigo_Programa', 'Nombre_Programa', 'Total_Estudiantes', 'Egresados_ULibre']
            resumen_año['Solo_Estudiantes'] = resumen_año['Total_Estudiantes'] - resumen_año['Egresados_ULibre']
            resumen_año['Porcentaje'] = (resumen_año['Egresados_ULibre'] / resumen_año['Total_Estudiantes'] * 100).round(2)
            resumen_año.to_excel(writer, sheet_name=f'Año {año}', index=False)
        
        df_consolidado.to_excel(writer, sheet_name='Consolidado', index=False)
    
    print(f"✓ Archivo Excel generado: {archivo_excel}")


def main():
    """
    Función principal
    """
    print("\n" + "="*80)
    print("ANÁLISIS DE EGRESADOS EN PROGRAMAS DE POSGRADO (2021-2025)")
    print("Identificando estudiantes con títulos PREVIOS de otros programas ULibre")
    print("="*80)
    
    # Directorios y archivos
    dir_base = Path(__file__).parent
    dir_entrada = dir_base / 'data' / 'posgrados_limpios'
    dir_salida = dir_base / 'output' / 'egresados-posgrados'
    ruta_bdd = dir_base / 'data' / 'posgrados' / 'BDD. 1974 ACTUALIZADA CON GRADOS DEL 14 DE NOVIEMBRE 2025 (1).csv'
    
    # Crear directorio de salida
    dir_salida.mkdir(parents=True, exist_ok=True)
    
    # Cargar base de datos de egresados con detalle de programas
    egresados_detalle = cargar_base_datos_egresados_detallada(ruta_bdd)
    
    if not egresados_detalle:
        print("❌ No se pudo cargar la base de datos de egresados")
        return
    
    # Procesar archivos limpios
    años = [2021, 2022, 2023, 2024, 2025]
    todos_resultados = []
    
    for año in años:
        archivo = dir_entrada / f'{año}-Posgrados-limpio.csv'
        
        if not archivo.exists():
            print(f"⚠️  Archivo no encontrado: {archivo}")
            continue
        
        resultados = procesar_archivo_limpio(archivo, egresados_detalle)
        todos_resultados.extend(resultados)
    
    # Generar reportes
    if todos_resultados:
        generar_reportes(todos_resultados, dir_salida)
        
        total_egresados = sum(1 for r in todos_resultados if r['Es_Egresado_ULibre'] == 'Sí')
        total_solo_estudiantes = len(todos_resultados) - total_egresados
        
        print(f"\n{'='*80}")
        print("PROCESO COMPLETADO EXITOSAMENTE")
        print(f"{'='*80}")
        print(f"\nArchivos generados en: {dir_salida}")
        print(f"Total de estudiantes analizados: {len(todos_resultados):,}")
        print(f"Egresados ULibre (con título previo de otro programa): {total_egresados:,} ({(total_egresados/len(todos_resultados)*100):.2f}%)")
        print(f"Solo estudiantes (sin título previo ULibre): {total_solo_estudiantes:,} ({(total_solo_estudiantes/len(todos_resultados)*100):.2f}%)")
    else:
        print("\n❌ No se procesaron registros")


if __name__ == "__main__":
    main()
