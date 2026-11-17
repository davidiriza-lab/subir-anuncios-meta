---
name: subir-anuncios-meta
description: Publica anuncios de Meta (Facebook e Instagram) con videos o imágenes que están en la computadora del usuario, desde Claude Code, con el MCP oficial de Meta Ads (subida directa o, de respaldo, un bucket puente de Supabase Storage). Usa cuando se mencione "sube este video como anuncio", "publica este anuncio", "crea un anuncio con esta imagen", "sube este creativo a Meta", "pon este video en mi cuenta publicitaria" o cualquier anuncio de Meta hecho con un archivo local.
---

# Subir anuncios a Meta con archivos locales

Hay dos formas de llevar un archivo de la computadora a Meta desde Claude Code. Revisa cuál tienes antes de empezar:

- **Subida directa (la normal).** Si tienes las herramientas `ads_create_upload_url` y `ads_finalize_upload`, el archivo va directo de la computadora a Meta. No necesita nada más. Acepta imágenes de hasta 30 MiB y videos de hasta 100 MiB.
- **Bucket puente (respaldo).** Si tu MCP de Meta no trae esas herramientas, o la subida directa falla, subes el archivo un momento a Supabase Storage, Meta lo baja con la liga pública y lo borras. Pide un proyecto de Supabase (ver "Primera vez", paso 2).

```
directa:  tu archivo → MCP de Meta → tu cuenta publicitaria
puente:   tu archivo → bucket puente (Supabase) → MCP de Meta → tu cuenta publicitaria → se borra del puente
```

Las ligas de Google Drive, Dropbox o Canva no sirven como liga pública: baja el archivo y súbelo por una de las dos rutas.

Los scripts del puente viven en `scripts/` junto a este archivo. Córrelos con su ruta completa, por ejemplo `python3 ~/.claude/skills/subir-anuncios-meta/scripts/subir.py`.

## Reglas de oro

1. **Todo se crea en PAUSED.** Campaña, conjunto y anuncio. Nunca actives nada (`ads_activate_entity`) sin que el usuario lo pida después de revisar.
2. **Si usaste el puente, siempre borra** lo que subiste, en cuanto Meta lo procese. También si el flujo falla a la mitad: borra antes de reportar el error.
3. **Confirma el presupuesto** antes de crear. Revisa con `ads_get_field_context` en qué unidad lo pide el campo (normalmente centavos: `50000` = 500.00).
4. **No inventes IDs** de intereses, páginas, pixeles ni cuentas. Sácalos de las herramientas del MCP.
5. **La llave de Supabase vive solo en el archivo de configuración.** Nunca la pongas en un comando ni la imprimas. Los scripts la leen de ahí.

## Primera vez

Revisa en este orden. Si todo ya está, pasa directo al flujo.

### 1. MCP de Meta conectado

¿Tienes herramientas que empiezan con `ads_` (por ejemplo `ads_get_ad_accounts`)? Si no, dile al usuario:

- Corre en la terminal: `claude mcp add --transport http meta-ads https://mcp.facebook.com/ads --scope user`
- Abre Claude Code de nuevo, escribe `/mcp`, elige `meta-ads` e inicia sesión con el Facebook que tiene acceso a tus cuentas publicitarias.

### 2. Configuración de Supabase (solo para el puente)

Sáltate este paso si tienes la subida directa (`ads_create_upload_url` y `ads_finalize_upload`). Hazlo solo si no la tienes, si falló, o si el usuario quiere el puente como respaldo.

Corre `python3 scripts/preparar.py`. Si dice que falta la configuración:

1. Pide al usuario que cree un proyecto gratis en https://supabase.com (o que use uno que ya tenga).
2. Pídele dos datos de **Project Settings → API Keys**:
   - la **URL del proyecto** (`https://xxxx.supabase.co`)
   - la **llave secret** (`sb_secret_...`) o, en proyectos viejos, la `service_role`. **No** la publishable ni la anon.
3. Escribe el archivo `~/.config/subir-anuncios-meta/config.json` con la herramienta para escribir archivos (no con `echo` ni `cat`, para que la llave no quede en un comando):
   ```json
   {
     "supabase_url": "https://xxxx.supabase.co",
     "supabase_key": "sb_secret_...",
     "bucket": "anuncios-meta"
   }
   ```
4. Ciérralo: `chmod 700 ~/.config/subir-anuncios-meta && chmod 600 ~/.config/subir-anuncios-meta/config.json`
5. Corre otra vez `python3 scripts/preparar.py`. Crea el bucket público `anuncios-meta` si no existe.

Si el usuario prefiere no pegar la llave en el chat, que cree él mismo ese archivo con un editor de texto.

## Flujo: publicar un anuncio con un archivo local

### 1. Junta lo que falta

Antes de subir nada, ten claro:

- **Cuenta publicitaria.** Si no la dicen: `ads_get_ad_accounts` y pregunta cuál. El ID va solo con números, sin `act_`.
- **¿Anuncio nuevo en campaña nueva, o dentro de un conjunto que ya existe?** Si es existente, búscalo con `ads_get_ad_entities`.
- **Objetivo y presupuesto** (si es campaña nueva), **país o región**, **texto del anuncio**, **titular**, **liga de destino** y **botón** (CTA).
- **Página de Facebook:** `ads_get_ad_account_pages`. **Instagram** (opcional): `ads_get_ig_accounts`.

Si falta algo que no puedes deducir, pregúntalo en un solo mensaje.

### 2. Sube el archivo a Meta

**Ruta directa** (si tienes `ads_create_upload_url`):

1. Saca el tamaño exacto en bytes: `stat -f %z "/ruta/al/video.mp4"` en Mac, `stat -c %s` en Linux.
2. `ads_create_upload_url` con `file_name` (el nombre tal como está en disco), `mime_type` (`image/jpeg`, `image/png`, `image/gif`, `video/mp4` o `video/quicktime`), `file_size` y `ad_account_id`.
3. Sube el archivo con el `curl` que describe esa herramienta, mandando **todos** los encabezados de `upload_headers` exactamente como llegaron y con `--data-binary @"/ruta/al/video.mp4"` (no `-d` ni `-F`). Una respuesta 200 trae `completion_token`. Cada liga sirve para un solo archivo.
4. `ads_finalize_upload` con el `completion_token` y el `ad_account_id`. Una imagen devuelve `hash` (es el `image_hash` del creativo); un video devuelve `video_id`.

Si la subida no da 200, lee `error_message`. Si la liga venció, pide otra. Si sigue fallando, usa el puente.

**Ruta del puente** (si no tienes la directa o falló). Necesita la configuración de "Primera vez", paso 2:

1. `python3 scripts/limpiar.py` borra lo que lleve más de 6 horas en el puente, por si una vez anterior falló el borrado.
2. `python3 scripts/subir.py "/ruta/al/video.mp4"` devuelve JSON con `nombre`, `url` y `media_type`. Guarda el `nombre`: lo necesitas para borrar. Si pesa más de 50 MB (límite del plan gratis de Supabase), el script te da el comando de `ffmpeg` para comprimirlo.
3. `ads_creative_upload_media` con `upload_source: "URL"`, `media_type` (`VIDEO` o `IMAGE`), `media_url` (la `url` del paso anterior) y `name`. Una imagen devuelve el `image_hash`; un video, el `video_id`.
4. En cuanto Meta tenga el archivo (imagen con `image_hash`, video en `ready`), bórralo: `python3 scripts/borrar.py <nombre> [<nombre-miniatura>]`. La liga pública puede seguir abriendo unos minutos por caché; es normal, el archivo ya no existe.

### 3. Espera el video y prepara su miniatura

- **Video:** revisa con `ads_get_ad_videos` pasando `video_ids: ["<video_id>"]` hasta que el estado sea `ready` (puede tardar uno o dos minutos). Sin `video_ids` la herramienta solo lista id y título, sin estado. No uses el video antes de `ready`; si el estado es `error`, `upload_failed` o `expired`, vuelve a subirlo.
- **Miniatura del video** (la pide el creativo): si el usuario no da una, saca un cuadro con `ffmpeg -ss 1 -i video.mp4 -frames:v 1 miniatura.jpg` y súbela como imagen por la misma ruta que usaste para el video. Si no hay `ffmpeg`, pide una imagen.

### 4. Arma el anuncio (todo en PAUSED)

Si es campaña nueva:

1. `ads_create_campaign` con el objetivo (`OUTCOME_SALES`, `OUTCOME_LEADS`, `OUTCOME_TRAFFIC`…) y `status: PAUSED`.
2. `ads_create_ad_set`. El `optimization_goal` sale de los válidos que devolvió la campaña. Si optimiza a conversiones necesita `promoted_object` con el pixel (`ads_get_datasets`).

Después, siempre:

3. `ads_create_creative` con el `video_id` + miniatura (o el `image_hash`), el `page_id`, el texto, titular, liga y CTA. Agrega la cuenta de Instagram si la quieren.
4. `ads_create_ad` con el `creative_id`, en `PAUSED`.
5. `ads_get_ad_preview` y muéstrale al usuario cómo se ve.

### 5. Reporta

Los IDs creados, que **todo está en pausa** y que lo revise en el Administrador de anuncios antes de pedir que se active.

## Si estás en Claude Desktop o claude.ai

Ahí también puedes usar `ads_creative_upload_media` con `upload_source: "LOCAL_FILE"`: se abre una ventana y el usuario elige el archivo. El resto del flujo (pasos 3 a 5) es igual.

## Errores comunes

| Lo que pasa | Arreglo |
|---|---|
| La subida directa no devuelve 200 | Lee `error_message`. Revisa que mandaste todos los encabezados de `upload_headers` sin cambiarlos, que usaste `--data-binary` y que `file_size` es el tamaño exacto. Si la liga venció, pide otra con `ads_create_upload_url`. Si sigue fallando, usa el puente. |
| El archivo pasa de 30 MiB (imagen) o 100 MiB (video) | Comprímelo con `ffmpeg` antes de subirlo. |
| No tienes `ads_create_upload_url` | Tu MCP de Meta no trae la subida directa: usa el puente ("Primera vez", paso 2). |
| `preparar.py` dice 401 o 403 | La llave es la publishable o la anon. Usa la secret (`sb_secret_...`) o la `service_role`. |
| Los scripts no conectan o Supabase dice que el proyecto está pausado | Los proyectos gratis se pausan tras una semana sin uso. El usuario lo reactiva desde el panel de supabase.com y se vuelve a correr `preparar.py`. |
| `subir.py` dice que el archivo pasa el límite | Comprímelo con el comando de `ffmpeg` que imprime, o sube el límite en Supabase (planes de pago). |
| `ads_creative_upload_media` no acepta la liga | ¿Es la liga `/object/public/...` que dio `subir.py`? ¿Ya la borraste? Vuelve a subir. |
| El video se queda en `processing` | Espera y vuelve a revisar con `ads_get_ad_videos` y `video_ids`. No armes el creativo hasta `ready`. |
| `ads_get_ad_videos` no trae el estado | Faltó `video_ids`: sin eso solo devuelve id y título. |
| "Performance goal isn't available" | El `optimization_goal` no va con ese objetivo, o falta `promoted_object` con el pixel. |
| "Facebook Page is Missing" | Faltó `page_id` en el creativo. |
| No hay herramientas `ads_` | El MCP no está conectado o falta iniciar sesión: ver "Primera vez", paso 1. |
