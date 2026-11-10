#!/usr/bin/env python3
"""Borra del bucket puente lo que se haya quedado olvidado.
Uso: python3 limpiar.py            (borra archivos con más de 6 horas)
     python3 limpiar.py --todo     (vacía el bucket)"""
import json
import sys
from datetime import datetime, timedelta, timezone

from _comun import cargar_config, json_post, storage

todo = "--todo" in sys.argv[1:]
cfg = cargar_config()
limite = datetime.now(timezone.utc) - timedelta(hours=6)

codigo, texto = json_post(cfg, f"object/list/{cfg['bucket']}", {
    "prefix": "", "limit": 1000, "sortBy": {"column": "created_at", "order": "asc"},
})
if codigo != 200:
    sys.exit(f"No pude listar el bucket ({codigo}): {texto}")

viejos = []
for o in json.loads(texto):
    if not o.get("id"):  # carpetas
        continue
    creado = datetime.fromisoformat(o["created_at"].replace("Z", "+00:00"))
    if todo or creado < limite:
        viejos.append(o["name"])

if not viejos:
    print("Nada que limpiar.")
    raise SystemExit(0)

codigo, texto = storage(
    cfg, "DELETE", f"object/{cfg['bucket']}",
    json.dumps({"prefixes": viejos}).encode(), "application/json",
)
if codigo != 200:
    sys.exit(f"No pude borrar ({codigo}): {texto}")
print(f"Borré {len(viejos)} archivo(s): {', '.join(viejos)}")
