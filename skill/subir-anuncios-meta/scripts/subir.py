#!/usr/bin/env python3
"""Sube un archivo local al bucket puente y devuelve su URL pública.
Uso: python3 subir.py "/ruta/al/video.mp4"
Imprime JSON: {"nombre": ..., "url": ..., "media_type": "VIDEO"|"IMAGE", "bytes": ...}"""
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from _comun import cargar_config, storage, url_publica

TIPOS = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif",
    ".mp4": "video/mp4", ".mov": "video/quicktime",
}

if len(sys.argv) != 2:
    sys.exit('Uso: python3 subir.py "/ruta/al/archivo"')

archivo = Path(sys.argv[1]).expanduser()
if not archivo.is_file():
    sys.exit(f"No existe el archivo: {archivo}")

ext = archivo.suffix.lower()
tipo = TIPOS.get(ext)
if not tipo:
    sys.exit(f"Formato {ext or '(sin extensión)'} no soportado. Usa JPG, PNG, GIF, MP4 o MOV.")

# Nombre único y seguro para URL: fecha-hora + nombre sin acentos ni espacios.
base = unicodedata.normalize("NFKD", archivo.stem).encode("ascii", "ignore").decode()
base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()[:60] or "archivo"
nombre = f"{datetime.now():%Y%m%d-%H%M%S}-{base}{ext}"

cfg = cargar_config()
datos = archivo.read_bytes()
codigo, texto = storage(cfg, "POST", f"object/{cfg['bucket']}/{nombre}", datos, tipo)

if codigo == 200:
    print(json.dumps({
        "nombre": nombre,
        "url": url_publica(cfg, nombre),
        "media_type": "VIDEO" if tipo.startswith("video/") else "IMAGE",
        "bytes": len(datos),
    }, ensure_ascii=False))
elif codigo == 413 or "maximum allowed size" in texto.lower():
    mb = len(datos) / 1024 / 1024
    sys.exit(
        f"El archivo pesa {mb:.0f} MB y pasa el límite de Supabase (50 MB en el plan gratis).\n"
        f"Comprímelo, por ejemplo:\n"
        f'  ffmpeg -i "{archivo}" -c:v libx264 -crf 26 -preset slow -c:a aac -b:a 128k "{archivo.with_suffix("")}-ligero.mp4"\n'
        f"o sube el límite en Supabase → Storage → Settings (planes de pago)."
    )
elif codigo == 404 and "bucket" in texto.lower():
    sys.exit(f"No existe el bucket '{cfg['bucket']}'. Corre primero: python3 preparar.py")
else:
    sys.exit(f"Falló la subida ({codigo}): {texto}")
