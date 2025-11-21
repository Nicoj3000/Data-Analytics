import pandas as pd
from pathlib import Path

# Rutas de los archivos
base_path = Path(__file__).parent / "ENCUESTAS 2021 - 2025 "
archivo_mo = base_path / "2021-2025(M0).csv"
archivo_ve = base_path / "2021-2025(VE).csv"

valores_unicos = set()

for archivo in [archivo_mo, archivo_ve]:
    if not archivo.exists():
        continue
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(archivo, 'r', encoding='latin-1') as f:
            lines = f.readlines()
    
    header_line = 0
    for i, line in enumerate(lines):
        if 'DOCUMENTO' in line and 'NOMBRES' in line:
            header_line = i
            break
    
    try:
        df = pd.read_csv(archivo, encoding='utf-8', sep=';', skiprows=header_line, on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(archivo, encoding='latin-1', sep=';', skiprows=header_line, on_bad_lines='skip')
    
    print(f"\n{'='*80}")
    print(f"Archivo: {archivo.name}")
    print('='*80)
    
    # Buscar columnas
    for col in df.columns:
        if 'INFORMACIÓN OCUPACIONAL' in col.upper() or 'INFORMACION OCUPACIONAL' in col.upper():
            print(f"\nColumna encontrada: '{col}'")
            valores = df[col].dropna().unique()
            print(f"Valores únicos ({len(valores)}):")
            for v in sorted(valores):
                count = len(df[df[col] == v])
                print(f"  - {v}: {count} registros")
                valores_unicos.add(str(v))

print(f"\n{'='*80}")
print("TODOS LOS VALORES ÚNICOS ENCONTRADOS:")
print('='*80)
for v in sorted(valores_unicos):
    print(f"  - {v}")
