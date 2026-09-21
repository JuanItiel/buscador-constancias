import platform
import shutil
import subprocess
from pathlib import Path

print("=" * 60)
print("  DIAGNÓSTICO DE GHOSTSCRIPT")
print("=" * 60)
print(f"Sistema operativo: {platform.system()} {platform.release()}")
print()

# 1. Buscar en el PATH
print("1️⃣  Buscando en el PATH...")
for nombre in ["gs", "gswin64c", "gswin32c", "gswin64c.exe", "gswin32c.exe"]:
    ruta = shutil.which(nombre)
    if ruta:
        print(f"   ✅ Encontrado: {nombre} → {ruta}")
    else:
        print(f"   ❌ No encontrado: {nombre}")
print()

# 2. Buscar en Program Files
print("2️⃣  Buscando en Program Files...")
rutas_buscar = [
    Path("C:/Program Files/gs"),
    Path("C:/Program Files (x86)/gs"),
    Path("C:/Program Files/GS"),
]
encontrado = False
for base in rutas_buscar:
    print(f"\n   📁 Revisando: {base}")
    if not base.exists():
        print(f"      ❌ No existe esta carpeta")
        continue
    print(f"      ✅ Existe. Contenido:")
    for item in sorted(base.iterdir()):
        print(f"         - {item.name}")
        if item.is_dir():
            bin_dir = item / "bin"
            if bin_dir.exists():
                for exe in bin_dir.iterdir():
                    if exe.suffix.lower() == ".exe":
                        print(f"            └─ {exe.name}  ({exe.stat().st_size/1024:.0f} KB)")
                        encontrado = True
print()

# 3. Buscar en todo el disco C: (por si está en otra ruta)
print("3️⃣  Buscando gswin64c.exe en C:\\ (puede tardar unos segundos)...")
try:
    resultado = subprocess.run(
        ["where", "/r", "C:\\", "gswin64c.exe"],
        capture_output=True, text=True, timeout=30
    )
    if resultado.stdout.strip():
        print("   ✅ Encontrado en:")
        for linea in resultado.stdout.strip().split("\n"):
            print(f"      {linea}")
        encontrado = True
    else:
        print("   ❌ No se encontró en C:\\")
except subprocess.TimeoutExpired:
    print("   ⏱ Búsqueda cancelada (tardó más de 30s)")
except Exception as e:
    print(f"   ⚠ Error: {e}")
print()

# 4. Verificar versiones
print("4️⃣  Verificando versiones de ejecutables encontrados...")
for nombre in ["gswin64c", "gswin32c", "gs"]:
    ruta = shutil.which(nombre)
    if ruta:
        try:
            v = subprocess.run([ruta, "--version"], capture_output=True, text=True, timeout=5)
            print(f"   ✅ {nombre}: versión {v.stdout.strip()}")
        except Exception as e:
            print(f"   ⚠ {nombre}: {e}")
print()

# 5. Resultado final
print("=" * 60)
if encontrado:
    print("✅ Ghostscript ESTÁ instalado. Copia la ruta completa del .exe")
    print("   y pégala abajo en el script como RUTA_GHOSTSCRIPT.")
else:
    print("❌ Ghostscript NO está instalado o está en una ruta rara.")
    print("   Descárgalo desde: https://www.ghostscript.com/releases/gsdnld.html")
    print("   Descarga el archivo: 'Ghostscript AGPL Release' (Windows 64-bit)")
print("=" * 60)