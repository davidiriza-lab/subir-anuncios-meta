# Subir anuncios a Meta desde Claude Code

Dile a Claude "sube este video como anuncio" y lo publica en tu cuenta de Meta con los archivos de tu computadora, en pausa para que lo revises.

Es una skill para Claude Code. Sube el video o la imagen, arma la campaña, el conjunto y el anuncio de Facebook e Instagram, y te enseña la vista previa. Nada se activa ni gasta dinero hasta que tú lo pides. Es para quien ya anuncia en Meta y quiere dejar de armar cada anuncio a mano; no necesitas saber programar, Claude la instala.

## Instalar: pega esto en Claude Code

```
Lee https://raw.githubusercontent.com/davidiriza-lab/subir-anuncios-meta/main/INSTALAR.md
y sigue sus instrucciones al pie de la letra.
```

Descarga la skill en `~/.claude/skills/subir-anuncios-meta/` y revisa que el MCP de Meta esté conectado. Si ya tenías la skill, te pregunta antes de actualizarla. Al terminar, abre Claude Code de nuevo.

## Qué necesitas

- **Claude Code.**
- **Una cuenta publicitaria de Meta** con su página de Facebook, y el Facebook con el que entras a ella.
- **El MCP oficial de Meta Ads**, conectado con ese Facebook. El instalador te da el comando y te dice cómo iniciar sesión.

Opcional:

- **`ffmpeg`**, para sacar la miniatura de los videos y comprimir los que pesan demasiado. Sin `ffmpeg`, Claude te pide una imagen para la miniatura.
- **Un proyecto de Supabase** (el plan gratis basta) y **Python 3.9 o más nuevo**. Solo hacen falta para el puente de respaldo; mira "Cómo funciona".

## Cómo se usa

Pídelo normal:

- "Sube `~/Desktop/hook-testimonio.mp4` como anuncio en mi cuenta Tienda, campaña de tráfico a mitienda.com, $200 diarios, México"
- "Agrega esta imagen como anuncio nuevo en el conjunto Remarketing 30d"
- "Publica estos tres videos como anuncios en la campaña Lanzamiento"
- "Ya lo revisé, activa el anuncio"

Claude te pregunta lo que falte (texto, titular, liga, botón), sube el archivo, arma todo en pausa y te muestra la vista previa.

## Qué trae

| Archivo | Qué es |
|---|---|
| `skill/subir-anuncios-meta/SKILL.md` | Las instrucciones que sigue Claude: primera vez, flujo completo y errores comunes. |
| `skill/subir-anuncios-meta/scripts/preparar.py` | Revisa la configuración y crea el bucket público si no existe. |
| `skill/subir-anuncios-meta/scripts/subir.py` | Sube un archivo al puente y devuelve su liga pública. |
| `skill/subir-anuncios-meta/scripts/borrar.py` | Borra archivos del puente. |
| `skill/subir-anuncios-meta/scripts/limpiar.py` | Borra lo que lleve más de 6 horas en el puente (o todo con `--todo`). |
| `INSTALAR.md` | Lo que sigue Claude cuando le pides instalarla. |

### Cómo funciona

Hay dos formas de llevar un archivo de tu computadora a Meta, y la skill escoge sola:

- **Subida directa.** El MCP oficial de Meta Ads ya trae herramientas para recibir un archivo desde Claude Code. Claude le pide a Meta una liga de subida, manda el archivo y Meta lo registra en tu cuenta. No necesitas nada más. Acepta imágenes de hasta 30 MiB y videos de hasta 100 MiB.
- **Bucket puente, de respaldo.** Si tu MCP todavía no trae esas herramientas o la subida directa falla, la skill sube el archivo unos minutos a un bucket de tu propio Supabase, Meta lo baja con la liga pública y la skill lo borra. Las ligas de Google Drive, Dropbox o Canva no le sirven a Meta.

```
directa:  tu archivo → MCP de Meta → tu cuenta publicitaria
puente:   tu archivo → bucket puente → MCP de Meta → tu cuenta publicitaria → se borra del puente
```

Esta skill nació con el puente porque antes era la única forma. La subida directa se agregó el 16 de noviembre de 2026 a partir de las herramientas que hoy publica el MCP de Meta; el puente es la ruta que tiene más pruebas reales.

### Reglas que sigue la skill

- **Todo se crea en pausa.** Nada gasta dinero hasta que lo revisas en el Administrador de anuncios y le pides que lo active.
- **Si usa el puente, siempre borra** lo que subió, aunque el flujo falle a la mitad.
- **Si configuras el puente, tu llave de Supabase no sale de tu computadora.** Vive en `~/.config/subir-anuncios-meta/config.json` (permisos 600) y los scripts la leen de ahí. Nunca va en un comando ni en este repo.

### Instalación a mano

```bash
D=~/.claude/skills/subir-anuncios-meta
mkdir -p "$D/scripts"
R=https://raw.githubusercontent.com/davidiriza-lab/subir-anuncios-meta/main/skill/subir-anuncios-meta
curl -fsSL "$R/SKILL.md" -o "$D/SKILL.md"
for f in _comun.py preparar.py subir.py borrar.py limpiar.py; do curl -fsSL "$R/scripts/$f" -o "$D/scripts/$f"; done
```

Para conectar el MCP de Meta:

```bash
claude mcp add --transport http meta-ads https://mcp.facebook.com/ads --scope user
```

Abre Claude Code de nuevo, escribe `/mcp`, elige `meta-ads` e inicia sesión con tu Facebook.

Solo si quieres el puente de respaldo, crea `~/.config/subir-anuncios-meta/config.json`:

```json
{
  "supabase_url": "https://xxxx.supabase.co",
  "supabase_key": "sb_secret_...",
  "bucket": "anuncios-meta"
}
```

Luego corre `chmod 600 ~/.config/subir-anuncios-meta/config.json` y `python3 ~/.claude/skills/subir-anuncios-meta/scripts/preparar.py`.

## Si algo falla

- **Claude dice que no tiene las herramientas de Meta.** Falta conectar el MCP o iniciar sesión: corre el comando de arriba, abre Claude Code de nuevo, escribe `/mcp`, elige `meta-ads` y entra con tu Facebook.
- **La subida directa falla.** Pídele a Claude "configura el puente": te pide los dos datos de tu Supabase y sube por ahí.
- **(Puente) `preparar.py` dice 401 o 403.** Pusiste la llave publishable o la anon. Va la secret (`sb_secret_...`) o, en proyectos viejos, la `service_role`.
- **(Puente) Los scripts no conectan con Supabase.** Los proyectos gratis se pausan tras una semana sin uso. Entra a supabase.com, reactiva el proyecto y vuelve a intentar.
- **El archivo pasa el límite.** La subida directa acepta imágenes de hasta 30 MiB y videos de hasta 100 MiB; el puente con el plan gratis de Supabase, hasta 50 MB por archivo. Claude te da el comando de `ffmpeg` para comprimir el video.
- **El video se queda "procesando".** Meta tarda uno o dos minutos. Claude espera a que esté listo antes de armar el anuncio.
- **Quedó algo en el puente.** Pídele a Claude "limpia el puente" o corre `python3 ~/.claude/skills/subir-anuncios-meta/scripts/limpiar.py --todo`.
- **Actualizar la skill.** Pega otra vez el texto de instalación. Tu configuración de Supabase no se toca.
- **¿Sin Claude ni MCP?** Si prefieres un script que publique el video directo con el API de Meta, usando tu propio token, mira [meta-ads-video-agente](https://github.com/davidiriza-lab/meta-ads-video-agente).

## Guía completa

Paso a paso: **https://davidiriza.com/lab/sube-anuncios-a-meta-desde-claude**

## Licencia

MIT. Hecho por [David Iriza](https://www.davidiriza.com/lab).
