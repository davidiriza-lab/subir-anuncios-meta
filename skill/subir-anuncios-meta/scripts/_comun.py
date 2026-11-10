"""Funciones compartidas por los scripts del bucket puente.

La llave de Supabase se lee de un archivo local y nunca se imprime.
Solo usa la librería estándar de Python (no hay que instalar nada).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

RUTA_CONFIG = Path(
    os.environ.get(
        "SUBIR_ANUNCIOS_META_CONFIG",
        Path.home() / ".config" / "subir-anuncios-meta" / "config.json",
    )
)

INSTRUCCIONES_CONFIG = f"""Falta la configuración en {RUTA_CONFIG}

Crea ese archivo con este contenido (y permisos 600):
{{
  "supabase_url": "https://TU-PROYECTO.supabase.co",
  "supabase_key": "tu llave secret (sb_secret_...) o service_role",
  "bucket": "anuncios-meta"
}}
Ver la sección "Primera vez" del SKILL.md."""


def cargar_config() -> dict:
    if not RUTA_CONFIG.exists():
        sys.exit(INSTRUCCIONES_CONFIG)
    try:
        cfg = json.loads(RUTA_CONFIG.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"{RUTA_CONFIG} no es JSON válido: {e}")
    for campo in ("supabase_url", "supabase_key"):
        if not str(cfg.get(campo, "")).strip():
            sys.exit(f"Falta '{campo}' en {RUTA_CONFIG}.\n\n{INSTRUCCIONES_CONFIG}")
    cfg["supabase_url"] = cfg["supabase_url"].strip().rstrip("/")
    cfg["supabase_key"] = cfg["supabase_key"].strip()
    cfg["bucket"] = str(cfg.get("bucket") or "anuncios-meta").strip()
    return cfg


def cabeceras(cfg: dict) -> dict:
    llave = cfg["supabase_key"]
    h = {"apikey": llave}
    # Las llaves viejas (service_role) son JWT y van también en Authorization.
    # Las nuevas (sb_secret_...) van solo en apikey.
    if llave.startswith("eyJ"):
        h["Authorization"] = f"Bearer {llave}"
    return h


def storage(cfg: dict, metodo: str, ruta: str, cuerpo: bytes | None = None,
            tipo: str | None = None, extra: dict | None = None) -> tuple[int, str]:
    """Llama al API de Storage. Devuelve (código HTTP, texto de respuesta)."""
    url = f"{cfg['supabase_url']}/storage/v1/{ruta.lstrip('/')}"
    h = cabeceras(cfg)
    if tipo:
        h["Content-Type"] = tipo
    if extra:
        h.update(extra)
    req = urllib.request.Request(url, data=cuerpo, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return codigo_real(e.code, e.read().decode(errors="replace"))
    except urllib.error.URLError as e:
        sys.exit(f"No pude conectar con {cfg['supabase_url']}: {e.reason}")


def codigo_real(codigo: int, texto: str) -> tuple[int, str]:
    """Storage a veces responde 400 con el código verdadero en el cuerpo
    ({"statusCode": "404", ...}). Devuelve ese código cuando existe."""
    try:
        interno = int(json.loads(texto).get("statusCode"))
        return interno, texto
    except (ValueError, TypeError, AttributeError):
        return codigo, texto


def json_post(cfg: dict, ruta: str, datos: dict) -> tuple[int, str]:
    return storage(cfg, "POST", ruta, json.dumps(datos).encode(), "application/json")


def url_publica(cfg: dict, nombre: str) -> str:
    return f"{cfg['supabase_url']}/storage/v1/object/public/{cfg['bucket']}/{nombre}"
