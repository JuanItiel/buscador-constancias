# -*- coding: utf-8 -*-
"""
preparar_constancias.py
-----------------------
Extrae el nombre de cada constancia PDF, comprime los archivos,
los renombra con el nombre de la persona y genera datos.json
para el buscador web.
"""

import re
import json
import shutil
import platform
import subprocess
from pathlib import Path

import pdfplumber

# ---------- DEPENDENCIAS OPCIONALES ----------
try:
    from tqdm import tqdm
    TIENE_TQDM = True
except ImportError:
    TIENE_TQDM = False

try:
    import pikepdf
    TIENE_PIKEPDF = True
except ImportError:
    TIENE_PIKEPDF = False


# ==================================================
# CONFIGURACIÓN
# ==================================================
CARPETA_ORIGINALES   = Path("./constancias_originales")
CARPETA_COMPRIMIDAS  = Path("./constancias")
ARCHIVO_JSON         = "datos.json"

# URL base donde estarán alojados los PDFs (edítala después de subir a GitHub/R2)
BASE_URL = "https://JuanItiel.github.io/buscador-constancias/constancias/"

METODO_COMPRESION    = "ghostscript"   # o "pikepdf"
PERFIL_GHOSTSCRIPT   = "ebook"         # screen | ebook | printer | prepress
GUARDAR_CADA         = 50


# ==================================================
# GHOSTSCRIPT: DETECCIÓN AUTOMÁTICA
# ==================================================
def encontrar_ghostscript():
    """Detecta la ruta de Ghostscript. Devuelve None si no lo encuentra."""
    # 🔴 RUTAS FIJAS conocidas (la tuya está aquí)
    rutas_conocidas = [
        r"C:\Program Files\gs\gs10.08.0\bin\gswin64c.exe",
    ]
    for ruta in rutas_conocidas:
        if Path(ruta).exists():
            return ruta

    # Búsqueda automática si la ruta fija falla
    if platform.system() == "Windows":
        for nombre in ["gswin64c", "gswin32c", "gs"]:
            ruta = shutil.which(nombre)
            if ruta:
                return ruta

        for base in [Path("C:/Program Files/gs"), Path("C:/Program Files (x86)/gs")]:
            if not base.exists():
                continue
            versiones = sorted(
                [d for d in base.iterdir() if d.is_dir() and d.name.lower().startswith("gs")],
                reverse=True
            )
            for v in versiones:
                for exe in ["gswin64c.exe", "gswin32c.exe", "gswin64.exe"]:
                    ruta = v / "bin" / exe
                    if ruta.exists():
                        return str(ruta)
        return None
    else:
        return shutil.which("gs")


# ==================================================
# COMPRESIÓN
# ==================================================
def comprimir_ghostscript(ruta_entrada, ruta_salida, perfil="ebook"):
    gs = encontrar_ghostscript()
    if not gs:
        return False, "Ghostscript no encontrado"

    cmd = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{perfil}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        f"-sOutputFile={ruta_salida}",
        str(ruta_entrada),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True, "ok"
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode(errors="ignore")[:200]
    except Exception as e:
        return False, str(e)[:200]


def comprimir_pikepdf(ruta_entrada, ruta_salida):
    if not TIENE_PIKEPDF:
        return False, "pikepdf no instalado"
    try:
        with pikepdf.open(ruta_entrada) as pdf:
            pdf.save(
                ruta_salida,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                linearize=True,
            )
        return True, "ok"
    except Exception as e:
        return False, str(e)[:200]


def comprimir_pdf(ruta_entrada, ruta_salida):
    if METODO_COMPRESION == "ghostscript":
        ok, msg = comprimir_ghostscript(ruta_entrada, ruta_salida, PERFIL_GHOSTSCRIPT)
        if ok:
            return True, "ghostscript"
        if TIENE_PIKEPDF:
            ok2, msg2 = comprimir_pikepdf(ruta_entrada, ruta_salida)
            if ok2:
                return True, "pikepdf (fallback)"
            return False, f"gs: {msg} | pikepdf: {msg2}"
        return False, f"gs: {msg}"

    elif METODO_COMPRESION == "pikepdf":
        ok, msg = comprimir_pikepdf(ruta_entrada, ruta_salida)
        if ok:
            return True, "pikepdf"
        ok2, msg2 = comprimir_ghostscript(ruta_entrada, ruta_salida, PERFIL_GHOSTSCRIPT)
        if ok2:
            return True, "ghostscript (fallback)"
        return False, f"pikepdf: {msg} | gs: {msg2}"

    return False, f"Método desconocido: {METODO_COMPRESION}"


# ==================================================
# EXTRACCIÓN
# ==================================================
def extraer_texto(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception as e:
        print(f"   ⚠ Error al leer PDF: {e}")
        return ""


def extraer_nombre(texto, inicio, fin):
    patron = rf"{re.escape(inicio)}(.*?){re.escape(fin)}"
    m = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
    return " ".join(m.group(1).split()) if m else None


def limpiar_nombre_archivo(nombre):
    limpio = re.sub(r'[\\/:*?"<>|]', '', nombre).strip()
    return re.sub(r"\s+", " ", limpio)


# ==================================================
# JSON
# ==================================================
def guardar_json(registros):
    datos = {
        "base_url": BASE_URL,
        "total": len(registros),
        "archivos": registros,
    }
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


# ==================================================
# MAIN
# ==================================================
def main():
    print("=" * 60)
    print("  PREPARADOR DE CONSTANCIAS")
    print("=" * 60)

    gs_path = encontrar_ghostscript()
    if gs_path:
        print(f"✅ Ghostscript encontrado: {gs_path}")
    else:
        print("⚠ Ghostscript NO encontrado. Se usará pikepdf si está instalado.")
        if not TIENE_PIKEPDF:
            print("❌ ERROR: ni Ghostscript ni pikepdf disponibles.")
            print("   Instala uno: pip install pikepdf")
            return

    if not CARPETA_ORIGINALES.exists():
        print(f"❌ No existe la carpeta: {CARPETA_ORIGINALES.resolve()}")
        return

    pdfs = sorted(CARPETA_ORIGINALES.glob("*.pdf"))
    if not pdfs:
        print(f"❌ No se encontraron PDFs en {CARPETA_ORIGINALES.resolve()}")
        return

    print(f"\n📁 Encontrados {len(pdfs)} PDFs.\n")

    # ---------- DEFINIR MARCADORES ----------
    primer_texto = extraer_texto(pdfs[0])
    print("=" * 60)
    print(f"📄 Texto de muestra: {pdfs[0].name}")
    print("=" * 60)
    print(primer_texto)
    print("=" * 60)

    INICIO = input("\n👉 El nombre empieza después de: ").strip()
    FIN    = input("👉 El nombre termina antes de: ").strip()

    if not INICIO or not FIN:
        print("❌ Debes definir ambos marcadores.")
        return

    # ---------- PROCESAR ----------
    CARPETA_COMPRIMIDAS.mkdir(exist_ok=True)

    registros = []
    errores = []
    stats = {"original_kb": 0, "comprimido_kb": 0, "metodos": {}}

    iterador = tqdm(pdfs, desc="Procesando", unit="pdf") if TIENE_TQDM else pdfs

    for i, pdf_path in enumerate(iterador, 1):
        texto = extraer_texto(pdf_path)
        nombre = extraer_nombre(texto, INICIO, FIN)

        if not nombre:
            errores.append(pdf_path.name)
            if not TIENE_TQDM:
                print(f"   ⚠ Sin nombre: {pdf_path.name}")
            continue

        nombre_limpio = limpiar_nombre_archivo(nombre)
        nombre_archivo = f"{nombre_limpio}.pdf"
        ruta_salida = CARPETA_COMPRIMIDAS / nombre_archivo

        ok, metodo = comprimir_pdf(pdf_path, ruta_salida)

        if not ok:
            shutil.copy2(pdf_path, ruta_salida)
            metodo = "sin comprimir"
            if not TIENE_TQDM:
                print(f"   ⚠ Copiado sin comprimir: {nombre_archivo}")

        try:
            tam_orig = pdf_path.stat().st_size
            tam_comp = ruta_salida.stat().st_size
            stats["original_kb"] += tam_orig / 1024
            stats["comprimido_kb"] += tam_comp / 1024
        except Exception:
            pass

        stats["metodos"][metodo] = stats["metodos"].get(metodo, 0) + 1

        registros.append({
            "nombre": nombre_limpio,
            "archivo": nombre_archivo,
        })

        if i % GUARDAR_CADA == 0:
            guardar_json(registros)

    guardar_json(registros)

    # ---------- RESUMEN ----------
    print("\n" + "=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    print(f"✅ Procesados:        {len(registros)}")
    print(f"⚠  Sin nombre:        {len(errores)}")
    print(f"📄 JSON generado:     {ARCHIVO_JSON}")
    print(f"📁 PDFs en:           {CARPETA_COMPRIMIDAS.resolve()}")

    if stats["original_kb"] > 0:
        ahorro = 100 * (1 - stats["comprimido_kb"] / stats["original_kb"])
        print(f"\n💾 Tamaño original:    {stats['original_kb']/1024:.2f} MB")
        print(f"💾 Tamaño comprimido:  {stats['comprimido_kb']/1024:.2f} MB")
        print(f"📉 Ahorro:             {ahorro:.1f}%")

    print(f"\n🔧 Métodos usados:")
    for m, c in stats["metodos"].items():
        print(f"   {m}: {c} archivos")

    if errores:
        print(f"\n⚠ Archivos sin nombre detectado:")
        for e in errores[:10]:
            print(f"   - {e}")
        if len(errores) > 10:
            print(f"   ... y {len(errores) - 10} más")

    print("\n✅ Listo.")


if __name__ == "__main__":
    main()