#!/usr/bin/env python3
"""Revisa la configuración y crea el bucket puente si no existe.
Uso: python3 preparar.py"""
import json

from _comun import cargar_config, json_post, storage

cfg = cargar_config()
bucket = cfg["bucket"]

codigo, texto = storage(cfg, "GET", f"bucket/{bucket}")
if codigo == 200:
    datos = json.loads(texto)
    if not datos.get("public"):
        codigo, texto = storage(
            cfg, "PUT", f"bucket/{bucket}",
            json.dumps({"public": True}).encode(), "application/json",
        )
        if codigo != 200:
            raise SystemExit(f"El bucket '{bucket}' existe pero es privado y no pude hacerlo público ({codigo}): {texto}")
        print(f"Bucket '{bucket}' ya existía; lo dejé público.")
    else:
        print(f"Listo: el bucket '{bucket}' ya existe y es público.")
    raise SystemExit(0)

LLAVE_EQUIVOCADA = (
    "Supabase rechazó la llave ({}). Usa la llave secret (sb_secret_...) o la service_role, "
    "no la publishable ni la anon.\nRespuesta: {}"
)
if codigo in (401, 403):
    raise SystemExit(LLAVE_EQUIVOCADA.format(codigo, texto))

codigo, texto = json_post(cfg, "bucket", {
    "id": bucket,
    "name": bucket,
    "public": True,
    "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "video/mp4", "video/quicktime"],
})
if codigo == 200:
    print(f"Listo: creé el bucket público '{bucket}'.")
elif codigo in (401, 403):
    raise SystemExit(LLAVE_EQUIVOCADA.format(codigo, texto))
else:
    raise SystemExit(f"No pude crear el bucket '{bucket}' ({codigo}): {texto}")
