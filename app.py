import pandas as pd
import numpy as np
from pathlib import Path
import re

def analizar_cargos_directivos():
    """
    Análisis profesional de cargos directivos en encuestas de egresados
    Universidad Libre - Pereira (2021-2025)
    """
    
    print("="*80)
    print("ANÁLISIS DE CARGOS DIRECTIVOS - ENCUESTAS EGRESADOS 2021-2025")
    print("Universidad Libre - Seccional Pereira")
    print("="*80)
    print()
    
    # Rutas de los archivos
    base_path = Path(__file__).parent / "ENCUESTAS 2021 - 2025 "
    archivo_mo = base_path / "2021-2025(M0).csv"
    archivo_ve = base_path / "2021-2025(VE).csv"  # IGNORE
    
    # Lista de palabras clave para identificar cargos directivos
    palabras_directivas = [
        'gerente', 'director', 'jefe', 'coordinador', 'supervisor',
        'presidente', 'vicepresidente', 'subdirector', 'subgerente',
        'juez', 'rector', 'juridico', 'lider', 'lider', 'administrador',
        'ejecutivo', 'manager', 'chief',
    ]
    
    resultados_totales = []
    
    # Procesar ambos archivos
    for archivo in [archivo_mo, archivo_ve]:
        if not archivo.exists():
            print(f"⚠️  Archivo no encontrado: {archivo.name}")
            continue
            
        print(f"\n📊 Procesando: {archivo.name}")
        print("-" * 80)
        
        try:
            # Leer el CSV con diferentes codificaciones
            # Primero detectar donde comienza la tabla de datos
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(archivo, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            
            # Encontrar la línea que contiene los encabezados (la que tiene "No;DOCUMENTO;...")
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
            
            # Mostrar columnas disponibles para debug
            print(f"📋 Columnas encontradas en el archivo:")
            for i, col in enumerate(df.columns[:10], 1):
                print(f"   {i}. {col}")
            if len(df.columns) > 10:
                print(f"   ... y {len(df.columns) - 10} columnas más")
            print()
            
            # Verificar si existe la columna de cargo (con diferentes encodings de ñ)
            columna_cargo = None
            variaciones_busqueda = [
                ('cargo', 'desempe'),  # Busca "cargo" y "desempe" (con ñ o �)
                ('cargo', 'desempe�a'),  # Con el caracter mal codificado
                ('cargo', 'desempena'),  # Sin la ñ
                ('cargo',)  # Solo "cargo"
            ]
            
            for variacion in variaciones_busqueda:
                if columna_cargo:
                    break
                for col in df.columns:
                    col_lower = col.lower()
                    if all(parte in col_lower for parte in variacion):
                        columna_cargo = col
                        print(f"✓ Columna de cargo encontrada: '{columna_cargo}'")
                        break
            
            if columna_cargo is None:
                print(f"❌ No se pudo identificar la columna de cargo")
                print(f"ℹ️  Columnas disponibles con 'cargo': {[c for c in df.columns if 'cargo' in c.lower()]}")
                continue
            
            # Filtrar datos válidos (eliminar NaN y vacíos)
            df_valido = df[df[columna_cargo].notna() & (df[columna_cargo] != '')]
            total_registros = len(df_valido)
            
            print(f"✓ Total de registros válidos con cargo: {total_registros}")
            
            # Identificar cargos directivos
            cargos_directivos = []
            
            for idx, row in df_valido.iterrows():
                cargo = str(row[columna_cargo]).lower()
                
                # Verificar si contiene palabras clave de cargo directivo
                es_directivo = any(palabra in cargo for palabra in palabras_directivas)
                
                if es_directivo:
                    cargos_directivos.append({
                        'Archivo': archivo.name,
                        'Nombre': f"{row.get('NOMBRES', '')} {row.get('APELLIDOS', '')}".strip(),
                        'Cargo': row[columna_cargo],
                        'Programa': row.get('PROGRAMA(S)', 'N/A'),
                        'Empresa': row.get('Nombre de la empresa', 'N/A')
                    })
            
            num_directivos = len(cargos_directivos)
            porcentaje = (num_directivos / total_registros * 100) if total_registros > 0 else 0
            
            print(f"✓ Cargos directivos identificados: {num_directivos}")
            print(f"✓ Porcentaje: {porcentaje:.2f}%")
            
            resultados_totales.extend(cargos_directivos)
            
            # Mostrar algunos ejemplos
            if num_directivos > 0:
                print(f"\n📋 Ejemplos de cargos directivos encontrados:")
                for i, cargo_info in enumerate(cargos_directivos[:5], 1):
                    print(f"   {i}. {cargo_info['Cargo']}")
                if num_directivos > 5:
                    print(f"   ... y {num_directivos - 5} más")
        
        except Exception as e:
            print(f"❌ Error al procesar {archivo.name}: {str(e)}")
    
    # Resumen general
    print("\n" + "="*80)
    print("RESUMEN GENERAL")
    print("="*80)
    
    if resultados_totales:
        print(f"\n📈 Total de cargos directivos identificados: {len(resultados_totales)}")
        
        # Crear DataFrame con los resultados
        df_resultados = pd.DataFrame(resultados_totales)
        
        # Análisis por tipo de cargo
        print(f"\n📊 Distribución por tipo de cargo:")
        print("-" * 80)
        
        tipos_cargo = {}
        for resultado in resultados_totales:
            cargo_lower = resultado['Cargo'].lower()
            for palabra in palabras_directivas:
                if palabra in cargo_lower:
                    tipos_cargo[palabra.capitalize()] = tipos_cargo.get(palabra.capitalize(), 0) + 1
        
        for tipo, cantidad in sorted(tipos_cargo.items(), key=lambda x: x[1], reverse=True):
            print(f"   {tipo:20s}: {cantidad:3d} personas")
        
        # Guardar resultados en CSV y Excel
        output_dir = Path(__file__).parent / "output" / "cargos-directivos"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        archivo_csv = output_dir / "cargos_directivos_analisis.csv"
        archivo_excel = output_dir / "cargos_directivos_analisis.xlsx"
        
        df_resultados.to_csv(archivo_csv, index=False, encoding='utf-8-sig')
        df_resultados.to_excel(archivo_excel, index=False, engine='openpyxl')
        
        print(f"\n💾 Resultados guardados exitosamente:")
        print(f"   📄 CSV: {archivo_csv.name}")
        print(f"   📗 Excel: {archivo_excel.name}")
        
        # Mostrar tabla detallada
        print(f"\n📋 LISTADO COMPLETO DE CARGOS DIRECTIVOS:")
        print("-" * 80)
        print(f"{'No.':<5} {'Nombre':<30} {'Cargo':<35}")
        print("-" * 80)
        
        for i, resultado in enumerate(resultados_totales, 1):
            nombre = resultado['Nombre'][:28] + '..' if len(resultado['Nombre']) > 30 else resultado['Nombre']
            cargo = resultado['Cargo'][:33] + '..' if len(resultado['Cargo']) > 35 else resultado['Cargo']
            print(f"{i:<5} {nombre:<30} {cargo:<35}")
    else:
        print("\n⚠️  No se encontraron cargos directivos en los archivos analizados.")
    
    print("\n" + "="*80)
    print("Análisis completado exitosamente")
    print("="*80)

if __name__ == "__main__":
    analizar_cargos_directivos()
