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

def analizar_por_programas_y_años():
    """
    Análisis de cargos directivos por programa y año de grado (2021-2025)
    Trabaja sobre el CSV de cargos directivos ya generado
    """
    
    print("="*80)
    print("ANÁLISIS DE CARGOS DIRECTIVOS POR PROGRAMA Y AÑO DE GRADO")
    print("Universidad Libre - Seccional Pereira (2021-2025)")
    print("="*80)
    print()
    
    # Ruta del archivo CSV ya procesado
    archivo_csv = Path(__file__).parent / "output" / "cargos-directivos" / "cargos_directivos_analisis.csv"
    
    if not archivo_csv.exists():
        print(f"❌ No se encontró el archivo: {archivo_csv.name}")
        print(f"   Por favor, ejecuta primero el script app.py para generar este archivo.")
        return
    
    print(f"📊 Procesando archivo: {archivo_csv.name}")
    print("-" * 80)
    
    resultados_detallados = []
    estadisticas_año = {2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0}
    estadisticas_programa = {}
    estadisticas_año_programa = {}
    
    try:
        # Leer el CSV de cargos directivos
        df = pd.read_csv(archivo_csv, encoding='utf-8-sig')
        
        print(f"✓ Total de cargos directivos en archivo: {len(df)}")
        print(f"✓ Columnas disponibles: {', '.join(df.columns)}")
        print()
        
        # Verificar que tenga la columna de Programa
        if 'Programa' not in df.columns:
            print(f"❌ No se encontró la columna 'Programa' en el archivo")
            return
        
        # Procesar cada registro
        registros_procesados = 0
        registros_unicos = set()  # Para evitar duplicados
        
        for idx, row in df.iterrows():
            programa_str = row.get('Programa', '')
            nombre = row.get('Nombre', '')
            
            # Extraer programas y fechas del string de programa
            programas_info = extraer_programas_y_fechas(programa_str)
            
            if programas_info:
                for prog_info in programas_info:
                    año = prog_info['año']
                    programa = prog_info['programa']
                    
                    # Crear clave única para evitar duplicados (mismo nombre, programa y año)
                    clave_unica = f"{nombre}_{programa}_{año}"
                    
                    if clave_unica not in registros_unicos:
                        registros_unicos.add(clave_unica)
                        
                        # Determinar tipo de programa
                        tipo_programa = 'PREGRADO'
                        if 'ESPECIALIZACIÓN' in programa.upper() or 'ESPECIALIZACION' in programa.upper():
                            tipo_programa = 'ESPECIALIZACIÓN'
                        elif 'MAESTRÍA' in programa.upper() or 'MAESTRIA' in programa.upper():
                            tipo_programa = 'MAESTRÍA'
                        elif 'DOCTORADO' in programa.upper():
                            tipo_programa = 'DOCTORADO'
                        
                        # Registrar resultado detallado
                        resultados_detallados.append({
                            'Archivo': row.get('Archivo', 'N/A'),
                            'Nombre': nombre,
                            'Cargo': row.get('Cargo', ''),
                            'Programa': programa,
                            'Tipo_Programa': tipo_programa,
                            'Año_Grado': año,
                            'Fecha_Grado': prog_info['fecha_completa'],
                            'Empresa': row.get('Empresa', 'N/A')
                        })
                        
                        # Actualizar estadísticas por año
                        if año in estadisticas_año:
                            estadisticas_año[año] += 1
                        
                        # Actualizar estadísticas por programa
                        if programa not in estadisticas_programa:
                            estadisticas_programa[programa] = 0
                        estadisticas_programa[programa] += 1
                        
                        # Actualizar estadísticas por año y programa
                        clave = f"{año}_{programa}"
                        if clave not in estadisticas_año_programa:
                            estadisticas_año_programa[clave] = {
                                'año': año,
                                'programa': programa,
                                'cantidad': 0
                            }
                        estadisticas_año_programa[clave]['cantidad'] += 1
                        
                        registros_procesados += 1
        
        print(f"✓ Registros únicos procesados (sin duplicados): {registros_procesados}")
        
    except Exception as e:
        print(f"❌ Error al procesar el archivo: {str(e)}")
        return
    
    # Mostrar resultados
    print("\n" + "="*80)
    print("RESULTADOS DEL ANÁLISIS")
    print("="*80)
    
    if resultados_detallados:
        print(f"\n📈 Total de cargos directivos identificados: {len(resultados_detallados)}")
        
        # Análisis por año
        print(f"\n📅 DISTRIBUCIÓN POR AÑO DE GRADO:")
        print("-" * 80)
        for año in sorted(estadisticas_año.keys()):
            cantidad = estadisticas_año[año]
            porcentaje = (cantidad / len(resultados_detallados) * 100) if len(resultados_detallados) > 0 else 0
            print(f"   {año}: {cantidad:4d} personas ({porcentaje:5.2f}%)")
        
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
        
        # Análisis cruzado: Año x Programa (Top combinaciones)
        print(f"\n📊 DISTRIBUCIÓN POR AÑO Y PROGRAMA (Top 30 combinaciones):")
        print("-" * 80)
        print(f"{'Año':<6} {'Programa':<50s} {'Cantidad':>10}")
        print("-" * 80)
        
        combinaciones_ordenadas = sorted(
            estadisticas_año_programa.values(),
            key=lambda x: (x['cantidad'], x['año']),
            reverse=True
        )
        
        for i, combo in enumerate(combinaciones_ordenadas[:30], 1):
            programa_corto = combo['programa'][:48] + '..' if len(combo['programa']) > 50 else combo['programa']
            print(f"{combo['año']:<6} {programa_corto:<50s} {combo['cantidad']:>10d}")
        
        if len(combinaciones_ordenadas) > 30:
            print(f"\n... y {len(combinaciones_ordenadas) - 30} combinaciones más")
        
        # Guardar resultados en archivos
        print(f"\n💾 Guardando resultados...")
        
        output_dir = Path(__file__).parent / "output" / "cargos-directivos"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        df_resultados = pd.DataFrame(resultados_detallados)
        
        # Archivo CSV general
        archivo_csv = output_dir / "cargos_directivos_por_programa_año.csv"
        df_resultados.to_csv(archivo_csv, index=False, encoding='utf-8-sig')
        print(f"   📄 CSV detallado: {archivo_csv.name}")
        
        # Archivo Excel con múltiples hojas
        archivo_excel = output_dir / "cargos_directivos_por_programa_año.xlsx"
        with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
            # Hoja 1: Datos completos
            df_resultados.to_excel(writer, sheet_name='Datos Completos', index=False)
            
            # Hoja 2: Resumen por año
            df_por_año = pd.DataFrame([
                {'Año': año, 'Cantidad': cantidad, 'Porcentaje': f"{cantidad/len(resultados_detallados)*100:.2f}%"}
                for año, cantidad in sorted(estadisticas_año.items())
            ])
            df_por_año.to_excel(writer, sheet_name='Por Año', index=False)
            
            # Hoja 3: Resumen por programa
            df_por_programa = pd.DataFrame([
                {'Programa': prog, 'Cantidad': cant, 'Porcentaje': f"{cant/len(resultados_detallados)*100:.2f}%"}
                for prog, cant in sorted(estadisticas_programa.items(), key=lambda x: x[1], reverse=True)
            ])
            df_por_programa.to_excel(writer, sheet_name='Por Programa', index=False)
            
            # Hoja 4: Cruce Año x Programa
            df_cruce = pd.DataFrame(combinaciones_ordenadas)
            df_cruce = df_cruce.rename(columns={'año': 'Año', 'programa': 'Programa', 'cantidad': 'Cantidad'})
            df_cruce.to_excel(writer, sheet_name='Año x Programa', index=False)
        
        print(f"   📗 Excel con análisis: {archivo_excel.name}")
        
        # Crear archivos CSV por año
        print(f"\n📁 Generando archivos por año...")
        for año in sorted(estadisticas_año.keys()):
            df_año = df_resultados[df_resultados['Año_Grado'] == año]
            if len(df_año) > 0:
                archivo_año = output_dir / f"cargos_directivos_{año}.csv"
                df_año.to_excel(archivo_año.with_suffix('.xlsx'), index=False, engine='openpyxl')
                print(f"   ✓ {año}: {len(df_año)} registros → {archivo_año.with_suffix('.xlsx').name}")
        
    else:
        print("\n⚠️  No se encontraron cargos directivos con programas válidos (2021-2025).")
    
    print("\n" + "="*80)
    print("Análisis completado exitosamente")
    print("="*80)

if __name__ == "__main__":
    analizar_por_programas_y_años()
