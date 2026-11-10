---
name: subir-anuncios-meta
description: Publica anuncios de Meta (Facebook e Instagram) con videos o imágenes que están en la computadora del usuario, desde Claude Code, usando el MCP oficial de Meta Ads y un bucket puente de Supabase Storage. Usa cuando se mencione "sube este video como anuncio", "publica este anuncio", "crea un anuncio con esta imagen", "sube este creativo a Meta", "pon este video en mi cuenta publicitaria" o cualquier anuncio de Meta hecho con un archivo local.
---

# Subir anuncios a Meta con archivos locales

El MCP oficial de Meta Ads solo puede tomar un archivo de la computadora en las apps que muestran su ventana para elegir archivos (Claude Desktop y claude.ai). En Claude Code no hay ventana, así que solo acepta **ligas públicas directas**. Las ligas de Google Drive, Dropbox o Canva no sirven.

La solución es un **bucket puente**: subes el archivo un momento a Supabase Storage, Meta lo baja con la liga pública y lo borras.

```
tu archivo → bucket puente (Supabase) → MCP de Meta → tu cuenta publicitaria → se borra del puente
```

Los scripts viven en `scripts/` junto a este archivo. Córrelos con su ruta completa, por ejemplo `python3 ~/.claude/skills/subir-anuncios-meta/scripts/subir.py`.

## Reglas de oro

1. **Todo se crea en PAUSED.** Campaña, conjunto y anuncio. Nunca actives nada (`ads_activate_entity`) sin que el usuario lo pida después de revisar.
2. **Siempre borra del puente** lo que subiste, en cuanto Meta lo procese. También si el flujo falla a la mitad: borra antes de reportar el error.
3. **Confirma el presupuesto** antes de crear. Revisa con `ads_get_field_context` en qué unidad lo pide el campo (normalmente centavos: `50000` = 500.00).
4. **No inventes IDs** de intereses, páginas, pixeles ni cuentas. Sácalos de las herramientas del MCP.
5. **La llave de Supabase vive solo en el archivo de configuración.** Nunca la pongas en un comando ni la imprimas. Los scripts la leen de ahí.

## Primera vez

Revisa en este orden. Si todo ya está, pasa directo al flujo.

### 1. MCP de Meta conectado

¿Tienes herramientas que empiezan con `ads_` (por ejemplo `ads_get_ad_accounts`)? Si no, dile al usuario:

- Corre en la terminal: `claude mcp add --transport http meta-ads https://mcp.facebook.com/ads --scope user`
- Abre Claude Code de nuevo, escribe `/mcp`, elige `meta-ads` e inicia sesión con el Facebook que tiene acceso a tus cuentas publicitarias.

### 2. Configuración de Supabase

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

### 0. Limpia lo olvidado

`python3 scripts/limpiar.py` borra lo que tenga más de 6 horas en el puente (por si una vez anterior falló el borrado).

### 1. Junta lo que falta

Antes de subir nada, ten claro:

- **Cuenta publicitaria.** Si no la dicen: `ads_get_ad_accounts` y pregunta cuál.
- **¿Anuncio nuevo en campaña nueva, o dentro de un conjunto que ya existe?** Si es existente, búscalo con `ads_get_ad_entities`.
- **Objetivo y presupuesto** (si es campaña nueva), **país o región**, **texto del anuncio**, **titular**, **liga de destino** y **botón** (CTA).
- **Página de Facebook:** `ads_get_ad_account_pages`. **Instagram** (opcional): `ads_get_ig_accounts`.

Si falta algo que no puedes deducir, pregúntalo en un solo mensaje.

### 2. Sube al puente

```bash
python3 scripts/subir.py "/ruta/al/video.mp4"
```

Devuelve JSON con `nombre`, `url` y `media_type`. Guarda el `nombre`: lo necesitas para borrar.

Si pesa más de 50 MB (límite del plan gratis de Supabase), el script te da el comando de `ffmpeg` para comprimirlo.

### 3. Súbelo a la biblioteca de Meta

`ads_creative_upload_media` con `upload_source: "URL"`, `media_type` (`VIDEO` o `IMAGE`), `media_url` (la `url` del paso 2) y `name`.

- **Imagen:** devuelve el `image_hash`.
- **Video:** devuelve el `video_id`. Revisa con `ads_get_ad_videos` hasta que el estado sea `ready` (puede tardar uno o dos minutos). No lo uses antes.
- **Miniatura del video** (la pide el creativo): si el usuario no da una, saca un cuadro con `ffmpeg -ss 1 -i video.mp4 -frames:v 1 miniatura.jpg`, súbela por el puente y luego a Meta como imagen. Si no hay `ffmpeg`, pide una imagen.

### 4. Borra del puente

En cuanto Meta tenga el archivo (imagen con `image_hash`, video en `ready`):

```bash
python3 scripts/borrar.py <nombre> [<nombre-miniatura>]
```

La liga pública puede seguir abriendo unos minutos por caché. Es normal: el archivo ya no existe.

### 5. Arma el anuncio (todo en PAUSED)

Si es campaña nueva:

1. `ads_create_campaign` con el objetivo (`OUTCOME_SALES`, `OUTCOME_LEADS`, `OUTCOME_TRAFFIC`…) y `status: PAUSED`.
2. `ads_create_ad_set`. El `optimization_goal` sale de los válidos que devolvió la campaña. Si optimiza a conversiones necesita `promoted_object` con el pixel (`ads_get_datasets`).

Después, siempre:

3. `ads_create_creative` con el `video_id` + miniatura (o el `image_hash`), el `page_id`, el texto, titular, liga y CTA. Agrega la cuenta de Instagram si la quieren.
4. `ads_create_ad` con el `creative_id`, en `PAUSED`.
5. `ads_get_ad_preview` y muéstrale al usuario cómo se ve.

### 6. Reporta

Los IDs creados, que **todo está en pausa** y que lo revise en el Administrador de anuncios antes de pedir que se active.

## Si estás en Claude Desktop o claude.ai

Ahí no necesitas el puente: usa `ads_creative_upload_media` con `upload_source: "LOCAL_FILE"`. Se abre una ventana y el usuario elige el archivo. El resto del flujo (pasos 3 a 6) es igual.

## Errores comunes

| Lo que pasa | Arreglo |
|---|---|
| `preparar.py` dice 401 o 403 | La llave es la publishable o la anon. Usa la secret (`sb_secret_...`) o la `service_role`. |
| `subir.py` dice que el archivo pasa el límite | Comprímelo con el comando de `ffmpeg` que imprime, o sube el límite en Supabase (planes de pago). |
| `ads_creative_upload_media` no acepta la liga | ¿Es la liga `/object/public/...` que dio `subir.py`? ¿Ya la borraste? Vuelve a subir. |
| El video se queda en `processing` | Espera y vuelve a revisar con `ads_get_ad_videos`. No armes el creativo hasta `ready`. |
| "Performance goal isn't available" | El `optimization_goal` no va con ese objetivo, o falta `promoted_object` con el pixel. |
| "Facebook Page is Missing" | Faltó `page_id` en el creativo. |
| No hay herramientas `ads_` | El MCP no está conectado o falta iniciar sesión: ver "Primera vez", paso 1. |
