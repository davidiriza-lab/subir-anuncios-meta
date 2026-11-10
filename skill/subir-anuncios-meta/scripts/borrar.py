#!/usr/bin/env python3
"""Borra uno o más archivos del bucket puente.
Uso: python3 borrar.py <nombre> [<nombre> ...]
El <nombre> es el que devolvió subir.py (no la ruta local)."""
import json
import sys

from _comun import cargar_config, storage

if len(sys.argv) < 2:
    sys.exit("Uso: python3 borrar.py <nombre> [<nombre> ...]")

cfg = cargar_config()
nombres = sys.argv[1:]
codigo, texto = storage(
    cfg, "DELETE", f"object/{cfg['bucket']}",
    json.dumps({"prefixes": nombres}).encode(), "application/json",
)
if codigo != 200:
    sys.exit(f"No pude borrar ({codigo}): {texto}")

borrados = {o.get("name") for o in json.loads(texto or "[]")}
for n in nombres:
    print(f"{'borrado' if n in borrados else 'no estaba'}: {n}")
