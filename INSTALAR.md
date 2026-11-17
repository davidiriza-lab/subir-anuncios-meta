# Instrucciones para Claude: instalar la skill subir-anuncios-meta

Sigue estos pasos en orden. Habla con el usuario en su idioma y sin tecnicismos. No pidas confirmación entre pasos salvo donde se indica. No instales dependencias: los scripts del puente solo usan Python 3 de serie.

Si leíste este archivo con una herramienta que resume páginas, bájalo completo antes de seguir, porque los comandos van tal cual:
`curl -fsSL https://raw.githubusercontent.com/davidiriza-lab/subir-anuncios-meta/main/INSTALAR.md`

Reglas para toda la instalación:

- **Nunca reemplaces algo que ya existe sin preguntar.** El paso 2 te dice cómo revisarlo. El archivo de configuración de Supabase, si ya existe, no se toca.
- El único dato sensible que puede pedirse es la llave de Supabase del usuario, y solo si configura el puente de respaldo. Va directo a su archivo de configuración. Nunca la pongas en un comando ni la repitas en el chat.
- No crees campañas ni anuncios durante la instalación.

## 1. Revisar el sistema

- `python3 --version` debe ser 3.9 o más nuevo. Solo lo usan los scripts del puente de respaldo: si no hay Python 3, avísale al usuario que el puente no va a funcionar hasta que lo instale y sigue con lo demás. En una Mac nueva, `python3` puede abrir una ventana que ofrece instalar las "herramientas de línea de comandos": que acepte, espere a que termine y vuelve a probar.
- `curl --version` debe responder.

## 2. Descargar la skill

**2.1 Bájala a una carpeta temporal** (todavía no se instala nada):

```bash
R=https://raw.githubusercontent.com/davidiriza-lab/subir-anuncios-meta/main/skill/subir-anuncios-meta
T="${TMPDIR:-/tmp}/subir-anuncios-meta"
mkdir -p "$T/scripts"
curl -fsSL "$R/SKILL.md" -o "$T/SKILL.md" || echo "FALLÓ SKILL.md"
for f in _comun.py preparar.py subir.py borrar.py limpiar.py; do
  curl -fsSL "$R/scripts/$f" -o "$T/scripts/$f" || echo "FALLÓ scripts/$f"
done
ls -la "$T" "$T/scripts"
```

Si algo dice `FALLÓ`, revisa la conexión y repite. No sigas con archivos incompletos.

**2.2 Revisa si ya estaba instalada:**

```bash
T="${TMPDIR:-/tmp}/subir-anuncios-meta"
D="$HOME/.claude/skills/subir-anuncios-meta"
if [ ! -e "$D" ]; then echo "NUEVO"
elif diff -rq -x __pycache__ "$T" "$D" >/dev/null; then echo "IGUAL"
else echo "DISTINTO"; diff -rq -x __pycache__ "$T" "$D"; fi
```

- `NUEVO`: instálala (2.3).
- `IGUAL`: ya la tiene al día. Sáltate 2.3.
- `DISTINTO`: ya tenía la skill y no es igual a esta. Puede ser una versión anterior o tener cambios suyos. Dile en una línea qué archivos cambian y pregúntale si la actualizas; aclárale que su configuración de Supabase vive aparte y no se toca. Si dice que sí, guarda antes una copia **fuera** de la carpeta de skills (para que Claude no cargue dos skills con el mismo nombre):
  ```bash
  mkdir -p ~/.claude/respaldos
  cp -R ~/.claude/skills/subir-anuncios-meta ~/.claude/respaldos/subir-anuncios-meta-$(date +%Y%m%d-%H%M%S)
  ```
  Si dice que no, deja la suya y sigue con el paso 3.

**2.3 Instala:**

```bash
T="${TMPDIR:-/tmp}/subir-anuncios-meta"
D="$HOME/.claude/skills/subir-anuncios-meta"
mkdir -p "$D/scripts"
cp "$T/SKILL.md" "$D/SKILL.md"
cp "$T"/scripts/*.py "$D/scripts/"
ls -la "$D" "$D/scripts"
```

## 3. Conectar Meta y decidir si hace falta el puente

Lee `~/.claude/skills/subir-anuncios-meta/SKILL.md`. Explica dos rutas: la subida directa (no pide nada más) y el puente de Supabase (respaldo).

1. **MCP de Meta.** Revisa si tienes herramientas que empiezan con `ads_` (por ejemplo `ads_get_ad_accounts`; si tus herramientas se cargan bajo demanda, búscala por ese nombre antes de decir que no está).
   - Si no las tienes, dale al usuario el comando para conectar el MCP de Meta (está en "Primera vez", paso 1 del SKILL.md) y explícale que después debe abrir Claude Code de nuevo y entrar a `/mcp` para iniciar sesión con Facebook. **No esperes a que lo haga**: déjalo como pendiente en el reporte.
2. **¿Subida directa o puente?**
   - Si tienes `ads_create_upload_url` y `ads_finalize_upload`, la subida directa está disponible y **no hace falta Supabase**. Pregúntale al usuario, en una línea, si de todos modos quiere dejar configurado el puente de respaldo; lo normal es que no.
   - Si el MCP está conectado pero no trae esas dos herramientas, hace falta el puente: sigue con el punto 3.
   - Si el MCP todavía no está conectado, no puedes saberlo: no pidas datos de Supabase ahora. Dile que, si al usarla la subida directa no está disponible, le pida a Claude "configura el puente".
3. **Puente (solo si hace falta o el usuario lo quiere).** Corre `python3 ~/.claude/skills/subir-anuncios-meta/scripts/preparar.py`.
   - Si dice "Listo", ya estaba configurado: no toques el archivo de configuración.
   - Si dice que falta la configuración, aquí sí espera al usuario: necesitas la URL de su proyecto y su llave secret. Escribe el archivo de configuración con la herramienta para escribir archivos, nunca con `echo` ni `cat`. Si prefiere no pegar la llave en el chat, que cree él mismo el archivo con el contenido que indica el SKILL.md.
   - Corre `preparar.py` otra vez hasta que diga "Listo".

## 4. Probar el puente (solo si lo configuraste)

Crea una imagen de prueba, súbela, revisa que la liga abra y bórrala. No necesita `ffmpeg` ni un archivo del usuario:

```bash
P="${TMPDIR:-/tmp}/prueba-puente.png"
python3 -c "import struct,sys,zlib;c=lambda t,d:struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d));open(sys.argv[1],'wb').write(b'\x89PNG\r\n\x1a\n'+c(b'IHDR',struct.pack('>IIBBBBB',16,16,8,2,0,0,0))+c(b'IDAT',zlib.compress((b'\0'+b'\xff\x8c\0'*16)*16))+c(b'IEND',b''))" "$P"
python3 ~/.claude/skills/subir-anuncios-meta/scripts/subir.py "$P"
```

Si la línea que crea la imagen falla, usa cualquier JPG o PNG chico del usuario. Del JSON que imprime `subir.py` toma `url` y `nombre`. Después:

1. `curl -sI "<url>"` debe dar 200.
2. `python3 ~/.claude/skills/subir-anuncios-meta/scripts/borrar.py <nombre>` debe decir `borrado`.

Si `subir.py` falla, lee su mensaje: dice qué falta (llave equivocada, bucket, conexión). La tabla de **Errores comunes** del SKILL.md tiene el arreglo de cada uno.

No pruebes la subida directa durante la instalación: registrar un archivo en la cuenta publicitaria ya es tocar la cuenta, y eso se hace cuando el usuario pida su primer anuncio.

## 5. Reportar

Dile al usuario en pocas líneas:

- qué quedó instalado y dónde,
- si quedó con subida directa, con puente, o si eso se sabrá cuando conecte el MCP (y si el puente pasó la prueba, cuando lo configuraste),
- si el MCP de Meta ya está conectado o qué le falta hacer (el comando, abrir Claude Code de nuevo y entrar a `/mcp`),
- que abra Claude Code de nuevo para que cargue la skill,
- y un ejemplo de cómo pedirlo: "sube ~/Desktop/video.mp4 como anuncio en mi cuenta X, tráfico a mi web, $200 diarios".
