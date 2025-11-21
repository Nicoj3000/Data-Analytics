import pandas as pd
import numpy as np
from pathlib import Path
import re
from datetime import datetime

def extraer_programas_y_fechas(programa_str):
    """
    Extrae programas y fechas de grado de la columna PROGRAMA(S)
    Formato: PROGRAMA( SECCIONAL )( FECHA ) - PROGRAMA2( SECCIONAL2 )( FECHA2 )
    Solo retorna programas con fechas entre 2021-2025
    """
    if pd.isna(programa_str) or programa_str == '':
        return []
    
    programas_info = []
    # Dividir por ' - ' para separar múltiples programas
    partes = str(programa_str).split(' - ')
    
    for parte in partes:
        # Buscar el patrón: NOMBRE_PROGRAMA( SECCIONAL )( FECHA )
        # Extraer fecha entre paréntesis
        patron_fecha = r'\(\s*(\d{4})-(\d{2})-(\d{2})\s*\)'
        matches_fecha = re.findall(patron_fecha, parte)
        
        if matches_fecha:
            # Tomar la última fecha encontrada (generalmente es la fecha de grado)
            año, mes, dia = matches_fecha[-1]
            año = int(año)
            
            # Solo considerar años entre 2021 y 2025
            if 2021 <= año <= 2025:
                # Extraer nombre del programa (todo antes del primer paréntesis)
                match_programa = re.match(r'^([^(]+)', parte)
                if match_programa:
                    nombre_programa = match_programa.group(1).strip()
                    programas_info.append({
                        'programa': nombre_programa,
                        'año': año,
                        'fecha_completa': f"{año}-{mes}-{dia}"
                    })
    
    return programas_info

def analizar_todos_egresados():
    """
    Análisis de TODOS los egresados por programa y año de grado (2021-2025)
    Trabaja directamente con los archivos CSV originales
    """
    
    print("="*80)
    print("ANÁLISIS DE TODOS LOS EGRESADOS POR PROGRAMA Y AÑO DE GRADO")
    print("Universidad Libre - Seccional Pereira (2021-2025)")
    print("="*80)
    print()
    
    # Rutas de los archivos
    base_path = Path(__file__).parent / "ENCUESTAS 2021 - 2025 "
    archivo_mo = base_path / "2021-2025(M0).csv"
    archivo_ve = base_path / "2021-2025(VE).csv"
    
    resultados_detallados = []
    estadisticas_año = {2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0}
    estadisticas_programa = {}
    estadisticas_año_programa = {}
    registros_unicos = {}  # Para evitar duplicados y mantener el más reciente
    
    # Procesar ambos archivos
    for archivo in [archivo_mo, archivo_ve]:
        if not archivo.exists():
            print(f"⚠️  Archivo no encontrado: {archivo.name}")
            continue
            
        print(f"\n📊 Procesando: {archivo.name}")
        print("-" * 80)
        
        try:
            # Leer el CSV con diferentes codificaciones
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(archivo, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            
            # Encontrar la línea que contiene los encabezados
            header_line = 0
            for i, line in enumerate(lines):
                if 'DOCUMENTO' in line and 'NOMBRES' in line:
                    header_line = i
                    break
            
            # Leer el CSV desde la línea de encabezados
            try:
                df = pd.read_csv(archivo, encoding='utf-8', sep=';', skiprows=header_line, on_bad_lines='skip')
            except UnicodeDecodeError:
                df = pd.read_csv(archivo, encoding='latin-1', sep=';', skiprows=header_line, on_bad_lines='skip')
            
            print(f"✓ Total de registros en archivo: {len(df)}")
            
            # Buscar columnas necesarias
            columna_programa = None
            columna_nombres = None
            columna_apellidos = None
            columna_documento = None
            columna_info_ocupacional = None
            columna_cargo = None
            columna_fecha_encuesta = None
            
            for col in df.columns:
                col_upper = col.upper()
                col_lower = col.lower()
                # Buscar específicamente PROGRAMA(S) - la columna correcta
                if col_upper == 'PROGRAMA(S)' or (col_upper.startswith('PROGRAMA') and '(' in col_upper and 'S)' in col_upper):
                    columna_programa = col
                elif 'NOMBRES' in col_upper and 'APELLIDOS' not in col_upper:
                    columna_nombres = col
                elif 'APELLIDOS' in col_upper:
                    columna_apellidos = col
                elif col_upper == 'DOCUMENTO':
                    columna_documento = col
                elif ('INFORMACI' in col_upper and 'OCUPACIONAL' in col_upper) and '(' not in col_upper:
                    # Buscar la columna INFORMACIÓN OCUPACIONAL (sin la parte de "(Actividad(es)...)")
                    columna_info_ocupacional = col
                elif 'CARGO' in col_upper and 'DESEMPE' in col_upper:
                    columna_cargo = col
                elif 'FECHA' in col_upper and 'ENCUESTA' in col_upper:
                    columna_fecha_encuesta = col
            
            if not columna_programa:
                print(f"❌ No se encontró la columna de PROGRAMA(S)")
                continue
            
            print(f"✓ Columna de programas encontrada: '{columna_programa}'")
            print()
            
            # Procesar cada registro
            registros_procesados = 0
            
            for idx, row in df.iterrows():
                programa_str = row.get(columna_programa, '')
                nombre = str(row.get(columna_nombres, '')).strip() if columna_nombres else ''
                apellido = str(row.get(columna_apellidos, '')).strip() if columna_apellidos else ''
                documento = str(row.get(columna_documento, '')).strip() if columna_documento else ''
                info_ocupacional = str(row.get(columna_info_ocupacional, '')).strip() if columna_info_ocupacional else ''
                cargo = str(row.get(columna_cargo, '')).strip() if columna_cargo else ''
                fecha_encuesta_str = str(row.get(columna_fecha_encuesta, '')).strip() if columna_fecha_encuesta else ''
                
                # Parsear fecha de encuesta
                fecha_encuesta = None
                if fecha_encuesta_str and fecha_encuesta_str != 'nan':
                    try:
                        # Intentar parsear diferentes formatos de fecha
                        fecha_encuesta = pd.to_datetime(fecha_encuesta_str, errors='coerce')
                    except:
                        pass
                
                nombre_completo = f"{nombre} {apellido}".strip()
                
                # Si no hay nombre, usar documento como identificador
                if not nombre_completo and documento:
                    nombre_completo = f"Doc_{documento}"
                
                # Extraer programas y fechas del string de programa
                programas_info = extraer_programas_y_fechas(programa_str)
                
                if programas_info:
                    for prog_info in programas_info:
                        año = prog_info['año']
                        programa = prog_info['programa']
                        
                        # Crear clave única para evitar duplicados (mismo nombre, programa y año)
                        clave_unica = f"{nombre_completo}_{programa}_{año}"
                        
                        # Determinar tipo de programa
                        tipo_programa = 'PREGRADO'
                        if 'ESPECIALIZACIÓN' in programa.upper() or 'ESPECIALIZACION' in programa.upper():
                            tipo_programa = 'ESPECIALIZACIÓN'
                        elif 'MAESTRÍA' in programa.upper() or 'MAESTRIA' in programa.upper():
                            tipo_programa = 'MAESTRÍA'
                        elif 'DOCTORADO' in programa.upper():
                            tipo_programa = 'DOCTORADO'
                        
                        # Crear registro temporal
                        registro_nuevo = {
                            'Archivo': archivo.name,
                            'Documento': documento,
                            'Nombre': nombre_completo,
                            'Programa': programa,
                            'Tipo_Programa': tipo_programa,
                            'Año_Grado': año,
                            'Fecha_Grado': prog_info['fecha_completa'],
                            'Información_Ocupacional': info_ocupacional,
                            'Cargo': cargo,
                            'Fecha_Encuesta': fecha_encuesta
                        }
                        
                        # Si la clave no existe, agregar directamente
                        if clave_unica not in registros_unicos:
                            registros_unicos[clave_unica] = registro_nuevo
                        else:
                            # Si ya existe, comparar fechas y quedarse con el más reciente
                            registro_existente = registros_unicos[clave_unica]
                            fecha_existente = registro_existente.get('Fecha_Encuesta')
                            
                            # Mantener el registro más reciente
                            if fecha_encuesta and fecha_existente:
                                if fecha_encuesta > fecha_existente:
                                    registros_unicos[clave_unica] = registro_nuevo
                            elif fecha_encuesta and not fecha_existente:
                                # Si el nuevo tiene fecha y el antiguo no, usar el nuevo
                                registros_unicos[clave_unica] = registro_nuevo
                        
                        registros_procesados += 1
            
            print(f"✓ Registros únicos procesados de este archivo: {registros_procesados}")
            
        except Exception as e:
            print(f"❌ Error al procesar el archivo {archivo.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # Procesar registros únicos y generar estadísticas
    print(f"\n✓ Total de registros procesados (incluye duplicados): {sum([len(registros_unicos)])} registros únicos")
    
    for clave_unica, registro in registros_unicos.items():
        # Remover la fecha de encuesta antes de agregar a resultados (no es necesaria en el Excel final)
        registro_limpio = {k: v for k, v in registro.items() if k != 'Fecha_Encuesta'}
        resultados_detallados.append(registro_limpio)
        
        # Actualizar estadísticas
        año = registro['Año_Grado']
        programa = registro['Programa']
        tipo_programa = registro['Tipo_Programa']
        
        # Estadísticas por año
        if año in estadisticas_año:
            estadisticas_año[año] += 1
        
        # Estadísticas por programa
        if programa not in estadisticas_programa:
            estadisticas_programa[programa] = 0
        estadisticas_programa[programa] += 1
        
        # Estadísticas por año y programa
        clave = f"{año}_{programa}"
        if clave not in estadisticas_año_programa:
            estadisticas_año_programa[clave] = {
                'año': año,
                'programa': programa,
                'tipo_programa': tipo_programa,
                'cantidad': 0
            }
        estadisticas_año_programa[clave]['cantidad'] += 1
    
    # Mostrar resultados
    print("\n" + "="*80)
    print("RESULTADOS DEL ANÁLISIS")
    print("="*80)
    
    if resultados_detallados:
        print(f"\n📈 Total de egresados únicos identificados: {len(resultados_detallados)}")
        
        # Análisis por año
        print(f"\n📅 DISTRIBUCIÓN POR AÑO DE GRADO:")
        print("-" * 80)
        for año in sorted(estadisticas_año.keys()):
            cantidad = estadisticas_año[año]
            porcentaje = (cantidad / len(resultados_detallados) * 100) if len(resultados_detallados) > 0 else 0
            print(f"   {año}: {cantidad:4d} egresados ({porcentaje:5.2f}%)")
        
        # Análisis por programa
        print(f"\n🎓 DISTRIBUCIÓN POR PROGRAMA (Top 20):")
        print("-" * 80)
        programas_ordenados = sorted(estadisticas_programa.items(), key=lambda x: x[1], reverse=True)
        for i, (programa, cantidad) in enumerate(programas_ordenados[:20], 1):
            porcentaje = (cantidad / len(resultados_detallados) * 100)
            # Truncar nombre del programa si es muy largo
            programa_corto = programa[:50] + '...' if len(programa) > 50 else programa
            print(f"   {i:2d}. {programa_corto:<53s}: {cantidad:4d} ({porcentaje:5.2f}%)")
        
        if len(programas_ordenados) > 20:
            print(f"   ... y {len(programas_ordenados) - 20} programas más")
        
        # Análisis cruzado: Año x Programa (Top 30 combinaciones)
        print(f"\n📊 DISTRIBUCIÓN POR AÑO Y PROGRAMA (Top 30 combinaciones):")
        print("-" * 80)
        print(f"{'Año':<6} {'Tipo':<15} {'Programa':<45s} {'Cantidad':>10}")
        print("-" * 80)
        
        combinaciones_ordenadas = sorted(
            estadisticas_año_programa.values(),
            key=lambda x: (x['cantidad'], x['año']),
            reverse=True
        )
        
        for i, combo in enumerate(combinaciones_ordenadas[:30], 1):
            programa_corto = combo['programa'][:43] + '..' if len(combo['programa']) > 45 else combo['programa']
            print(f"{combo['año']:<6} {combo['tipo_programa']:<15} {programa_corto:<45s} {combo['cantidad']:>10d}")
        
        if len(combinaciones_ordenadas) > 30:
            print(f"\n   ... y {len(combinaciones_ordenadas) - 30} combinaciones más")
        
        # Exportar resultados a CSV y Excel
        print("\n" + "="*80)
        print("EXPORTANDO RESULTADOS")
        print("="*80)
        
        # Crear DataFrame con todos los resultados
        df_resultados = pd.DataFrame(resultados_detallados)
        
        # Ordenar por año y programa
        df_resultados = df_resultados.sort_values(['Año_Grado', 'Programa', 'Nombre'])
        
        # Crear directorio de salida
        output_dir = Path(__file__).parent / "output" / "todos-egresados"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Exportar CSV con todos los datos
        archivo_csv = output_dir / "todos_egresados_por_programa_año.csv"
        df_resultados.to_csv(archivo_csv, index=False, encoding='utf-8-sig')
        print(f"✓ Archivo CSV exportado: {archivo_csv.name}")
        
        # 2. Crear resumen por año
        resumen_año = []
        for año in sorted(estadisticas_año.keys()):
            resumen_año.append({
                'Año': año,
                'Total_Egresados': estadisticas_año[año],
                'Porcentaje': round(estadisticas_año[año] / len(resultados_detallados) * 100, 2)
            })
        df_resumen_año = pd.DataFrame(resumen_año)
        
        # 3. Crear resumen por programa
        resumen_programa = []
        for programa, cantidad in sorted(estadisticas_programa.items(), key=lambda x: x[1], reverse=True):
            resumen_programa.append({
                'Programa': programa,
                'Total_Egresados': cantidad,
                'Porcentaje': round(cantidad / len(resultados_detallados) * 100, 2)
            })
        df_resumen_programa = pd.DataFrame(resumen_programa)
        
        # 4. Crear resumen cruzado año x programa
        resumen_año_programa = []
        for combo in sorted(estadisticas_año_programa.values(), key=lambda x: (x['año'], x['cantidad']), reverse=True):
            resumen_año_programa.append({
                'Año': combo['año'],
                'Programa': combo['programa'],
                'Tipo_Programa': combo['tipo_programa'],
                'Total_Egresados': combo['cantidad']
            })
        df_resumen_año_programa = pd.DataFrame(resumen_año_programa)
        
        # 5. Exportar Excel con múltiples hojas
        archivo_excel = output_dir / "todos_egresados_por_programa_año.xlsx"
        
        with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
            df_resultados.to_excel(writer, sheet_name='Datos Completos', index=False)
            df_resumen_año.to_excel(writer, sheet_name='Por Año', index=False)
            df_resumen_programa.to_excel(writer, sheet_name='Por Programa', index=False)
            df_resumen_año_programa.to_excel(writer, sheet_name='Año x Programa', index=False)
        
        print(f"✓ Archivo Excel exportado: {archivo_excel.name}")
        print(f"  - Hoja 1: Datos Completos ({len(df_resultados)} registros)")
        print(f"  - Hoja 2: Resumen por Año ({len(df_resumen_año)} años)")
        print(f"  - Hoja 3: Resumen por Programa ({len(df_resumen_programa)} programas)")
        print(f"  - Hoja 4: Resumen Año x Programa ({len(df_resumen_año_programa)} combinaciones)")
        
        # 6. Exportar archivos individuales por año
        print(f"\n📁 Generando archivos por año...")
        for año in sorted(estadisticas_año.keys()):
            df_año = df_resultados[df_resultados['Año_Grado'] == año]
            if len(df_año) > 0:
                archivo_año = output_dir / f"todos_egresados_{año}.xlsx"
                df_año.to_excel(archivo_año, index=False, engine='openpyxl')
                print(f"   ✓ {año}: {len(df_año)} egresados → {archivo_año.name}")
        
        print("\n" + "="*80)
        print("PROCESO COMPLETADO EXITOSAMENTE")
        print("="*80)
        print(f"\n📊 Resumen final:")
        print(f"   - Total de egresados únicos: {len(resultados_detallados)}")
        print(f"   - Años analizados: 2021-2025")
        print(f"   - Programas diferentes: {len(estadisticas_programa)}")
        print(f"   - Archivos generados: 8 (1 CSV + 6 Excel + 1 Excel resumen)")
        
    else:
        print("\n⚠️  No se encontraron egresados para analizar")
        print("   Verifica que los archivos CSV contengan datos válidos")

if __name__ == "__main__":
    try:
        analizar_todos_egresados()
    except Exception as e:
        print(f"\n❌ Error general en el análisis: {str(e)}")
        import traceback
        traceback.print_exc()
