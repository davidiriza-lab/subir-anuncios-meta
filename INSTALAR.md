# Instrucciones para Claude: instalar la skill subir-anuncios-meta

Sigue estos pasos en orden. No pidas confirmación entre pasos salvo donde se indica. No instales dependencias: los scripts solo usan Python 3 de serie.

## 1. Descargar la skill

```bash
D=~/.claude/skills/subir-anuncios-meta
mkdir -p "$D/scripts"
R=https://raw.githubusercontent.com/davidiriza-lab/subir-anuncios-meta/main/skill/subir-anuncios-meta
curl -fsSL "$R/SKILL.md" -o "$D/SKILL.md"
for f in _comun.py preparar.py subir.py borrar.py limpiar.py; do
  curl -fsSL "$R/scripts/$f" -o "$D/scripts/$f"
done
ls -la "$D" "$D/scripts"
```

Si ya existía `~/.claude/skills/subir-anuncios-meta`, avísale al usuario que se actualizó.

## 2. Revisar Python

`python3 --version` debe ser 3.9 o más nuevo. Si no hay Python 3, dile al usuario cómo instalarlo en su sistema y detente.

## 3. Hacer la "Primera vez"

Lee `~/.claude/skills/subir-anuncios-meta/SKILL.md` y sigue su sección **Primera vez**:

1. Revisa si tienes herramientas que empiezan con `ads_`. Si no, dale al usuario el comando para conectar el MCP de Meta y explícale que después debe abrir Claude Code de nuevo y entrar a `/mcp` para iniciar sesión con Facebook.
2. Configura Supabase. Aquí sí espera al usuario: necesitas su URL de proyecto y su llave secret. Escribe el archivo de configuración con la herramienta para escribir archivos, nunca con `echo`.
3. Corre `python3 ~/.claude/skills/subir-anuncios-meta/scripts/preparar.py` hasta que diga "Listo".

## 4. Probar el puente

Crea una imagen de prueba (con `ffmpeg -f lavfi -i color=c=orange:s=320x320 -frames:v 1 prueba.jpg` si hay ffmpeg, o cualquier JPG del usuario), súbela con `subir.py`, abre la `url` con `curl -sI` (debe dar 200) y bórrala con `borrar.py`.

## 5. Reportar

Dile al usuario en pocas líneas:

- qué quedó instalado y dónde,
- si el MCP de Meta ya está conectado o qué le falta hacer,
- que abra Claude Code de nuevo para que cargue la skill,
- y un ejemplo de cómo pedirlo: "sube ~/Desktop/video.mp4 como anuncio en mi cuenta X, tráfico a mi web, $200 diarios".
