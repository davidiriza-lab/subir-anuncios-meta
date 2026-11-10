# Subir anuncios a Meta desde Claude Code

Una skill para que Claude Code publique anuncios de Facebook e Instagram con los videos e imágenes que tienes en tu computadora. Le dices "sube este video como anuncio en mi cuenta" y él lo sube, arma la campaña y te la deja **en pausa** para que la revises.

## El problema que resuelve

El MCP oficial de Meta Ads deja elegir un archivo de tu computadora solo en Claude Desktop y claude.ai, porque ahí abre una ventana para escogerlo. En Claude Code (terminal o VS Code) no hay ventana, y el MCP solo acepta **ligas públicas directas**. Las ligas de Google Drive, Dropbox o Canva no le sirven.

La skill usa un **bucket puente** en Supabase Storage (gratis):

```
tu archivo → bucket puente → MCP de Meta → tu cuenta publicitaria → se borra del puente
```

El archivo vive en el puente solo unos minutos. Si algo falla, un script de limpieza borra lo que se haya quedado.

## Lo que necesitas

- **Claude Code**
- **El MCP oficial de Meta Ads**, conectado con tu Facebook (el instalador te dice cómo)
- **Un proyecto de Supabase**, el plan gratis basta. De ahí necesitas la URL del proyecto y la llave secret.
- Python 3.9 o más nuevo (ya viene en Mac). Opcional: `ffmpeg`, para sacar la miniatura de los videos y comprimir los que pesan más de 50 MB.

## Instalar: pídeselo a Claude

Pega esto en Claude Code:

```
Lee https://raw.githubusercontent.com/davidiriza-lab/subir-anuncios-meta/main/INSTALAR.md
y sigue sus instrucciones al pie de la letra.
```

Descarga la skill en `~/.claude/skills/subir-anuncios-meta/`, revisa que el MCP de Meta esté conectado, te pide los dos datos de Supabase, crea el bucket y hace una prueba de subida y borrado. Al terminar, abre Claude Code de nuevo.

## Usarla

Pídelo normal:

- "Sube `~/Desktop/hook-testimonio.mp4` como anuncio en mi cuenta Tienda, campaña de tráfico a mitienda.com, $200 diarios, México"
- "Agrega esta imagen como anuncio nuevo en el conjunto Remarketing 30d"
- "Publica estos tres videos como anuncios en la campaña Lanzamiento"

Claude te pregunta lo que falte (texto, titular, liga, botón), sube el archivo, arma todo y te muestra la vista previa.

## Reglas que sigue la skill

- **Todo se crea en pausa.** Nada gasta dinero hasta que lo revisas en el Administrador de anuncios y le pides que lo active.
- **Siempre borra del puente** lo que subió, aunque el flujo falle a la mitad.
- **Tu llave de Supabase no sale de tu computadora.** Vive en `~/.config/subir-anuncios-meta/config.json` (permisos 600) y los scripts la leen de ahí. Nunca va en un comando ni en este repo.

## Qué hay en este repo

| Archivo | Qué es |
|---|---|
| `skill/subir-anuncios-meta/SKILL.md` | Las instrucciones que sigue Claude: primera vez, flujo completo y errores comunes. |
| `skill/subir-anuncios-meta/scripts/preparar.py` | Revisa la configuración y crea el bucket público si no existe. |
| `skill/subir-anuncios-meta/scripts/subir.py` | Sube un archivo al puente y devuelve su liga pública. |
| `skill/subir-anuncios-meta/scripts/borrar.py` | Borra archivos del puente. |
| `skill/subir-anuncios-meta/scripts/limpiar.py` | Borra lo que lleve más de 6 horas en el puente (o todo con `--todo`). |
| `INSTALAR.md` | Lo que sigue Claude cuando le pides instalarla. |

## Instalación a mano

```bash
D=~/.claude/skills/subir-anuncios-meta
mkdir -p "$D/scripts"
R=https://raw.githubusercontent.com/davidiriza-lab/subir-anuncios-meta/main/skill/subir-anuncios-meta
curl -fsSL "$R/SKILL.md" -o "$D/SKILL.md"
for f in _comun.py preparar.py subir.py borrar.py limpiar.py; do curl -fsSL "$R/scripts/$f" -o "$D/scripts/$f"; done
```

Después crea `~/.config/subir-anuncios-meta/config.json`:

```json
{
  "supabase_url": "https://xxxx.supabase.co",
  "supabase_key": "sb_secret_...",
  "bucket": "anuncios-meta"
}
```

Luego corre `chmod 600 ~/.config/subir-anuncios-meta/config.json` y `python3 ~/.claude/skills/subir-anuncios-meta/scripts/preparar.py`.

Para conectar el MCP de Meta:

```bash
claude mcp add --transport http meta-ads https://mcp.facebook.com/ads --scope user
```

Abre Claude Code de nuevo, escribe `/mcp`, elige `meta-ads` e inicia sesión con tu Facebook.

## ¿Sin Claude ni MCP?

Si prefieres un script que publique el video directo con el API de Meta, usando tu propio token, mira [meta-ads-video-agente](https://github.com/davidiriza-lab/meta-ads-video-agente).

## Licencia

MIT
