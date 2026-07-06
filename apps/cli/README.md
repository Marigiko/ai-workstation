# AI Workstation CLI

Interfaz de línea de comandos para interactuar con la plataforma AI Workstation.

## Instalación

### Opción 1: Usar con `uv run` (Recomendado)

No requiere instalación adicional. Simplemente usa:

```bash
uv run ai <comando>
```

### Opción 2: Instalación Global

#### Windows (PowerShell)

1. Abre PowerShell como Administrador
2. Ejecuta:

```powershell
# Agregar el directorio de scripts de uv al PATH
$uvScriptsPath = "$env:LOCALAPPDATA\uv\tools"
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$uvScriptsPath*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$uvScriptsPath", "User")
}

# Reiniciar PowerShell o ejecutar:
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

3. Verifica la instalación:

```powershell
ai --help
```

#### Linux/Mac

1. Edita tu archivo de configuración de shell (`~/.bashrc`, `~/.zshrc`, o `~/.config/fish/config.fish`):

**Bash/Zsh:**
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Fish:**
```fish
set -gx PATH $HOME/.local/bin $PATH
```

2. Recarga la configuración:

```bash
source ~/.bashrc  # o ~/.zshrc
```

3. Verifica la instalación:

```bash
ai --help
```

## Comandos

### `ai status`

Verifica el estado del gateway.

```bash
uv run ai status
```

### `ai chat`

Envía un mensaje al LLM.

```bash
uv run ai chat "¿Qué es Python?"
uv run ai chat "Explica este código" --session <session-id>
```

**Opciones:**
- `--session`, `-s`: ID de sesión para continuar una conversación

### `ai session`

Gestiona sesiones de conversación.

```bash
# Crear sesión
uv run ai session create --title "Mi Proyecto"

# Listar sesiones
uv run ai session list --limit 10

# Ver detalles de sesión
uv run ai session show <session-id>

# Eliminar sesión
uv run ai session delete <session-id>
```

### `ai tools`

Gestiona y ejecuta herramientas.

```bash
# Listar herramientas disponibles
uv run ai tools list

# Ejecutar herramienta
uv run ai tools exec filesystem --params '{"operation": "read", "path": "/test.txt"}'
```

**Opciones para `exec`:**
- `--params`, `-p`: Parámetros JSON para la herramienta

### `ai skills`

Gestiona y ejecuta skills.

```bash
# Listar skills disponibles
uv run ai skills list

# Ejecutar skill
uv run ai skills exec code-review --vars '{"code": "def test(): pass"}'
```

**Opciones para `exec`:**
- `--vars`, `-v`: Variables JSON para el skill
- `--context`, `-c`: Contexto adicional

### `ai memory`

Gestiona la memoria persistente.

```bash
# Guardar memoria
uv run ai memory remember "Usuario prefiere Python" --scope global

# Recuperar memorias
uv run ai memory recall "preferencias Python" --scope global --limit 5
```

**Opciones para `remember`:**
- `--scope`, `-s`: Alcance (global, project, session)
- `--project`, `-p`: ID del proyecto (para scope project)
- `--session`: ID de sesión (para scope session)

**Opciones para `recall`:**
- `--scope`, `-s`: Alcance (global, project, session)
- `--limit`, `-l`: Número máximo de resultados
- `--project`, `-p`: ID del proyecto
- `--session`: ID de sesión

### `ai eval`

Evalúa la calidad de respuestas.

```bash
uv run ai eval run \
  --query "¿Qué es Python?" \
  --response "Python es un lenguaje de programación" \
  --metrics relevance,grounding,faithfulness
```

**Opciones:**
- `--query`, `-q`: Pregunta original
- `--response`, `-r`: Respuesta a evaluar
- `--metrics`, `-m`: Métricas separadas por comas

### `ai metrics`

Muestra métricas de observabilidad.

```bash
uv run ai metrics
```

## Configuración

### Variable de Entorno

Configura la URL del gateway:

```bash
# Linux/Mac
export GATEWAY_URL=http://localhost:8000

# Windows (PowerShell)
$env:GATEWAY_URL = "http://localhost:8000"

# Windows (CMD)
set GATEWAY_URL=http://localhost:8000
```

## Ejemplos de Uso

### Flujo de Trabajo Típico

```bash
# 1. Verificar estado del gateway
uv run ai status

# 2. Crear una sesión
uv run ai session create --title "Análisis de Código"

# 3. Chat con contexto
uv run ai chat "¿Puedes revisar este código?" --session <session-id>

# 4. Ejecutar skill de code review
uv run ai skills exec code-review --vars '{"code": "def add(a, b): return a + b"}'

# 5. Guardar hallazgos en memoria
uv run ai memory remember "El código sigue buenas prácticas" --scope project --project my-project

# 6. Ver métricas
uv run ai metrics
```

### Uso de Herramientas

```bash
# Leer un archivo
uv run ai tools exec filesystem --params '{"operation": "read", "path": "/path/to/file.py"}'

# Listar directorio
uv run ai tools exec filesystem --params '{"operation": "list", "path": "/path/to/dir"}'

# Ejecutar comando git
uv run ai tools exec git --params '{"command": "status", "cwd": "/path/to/repo"}'
```

### Evaluación de Respuestas

```bash
# Evaluar con múltiples métricas
uv run ai eval run \
  --query "¿Cómo funciona la recursión?" \
  --response "La recursión es cuando una función se llama a sí misma..." \
  --metrics relevance,grounding,faithfulness,completeness
```

## Troubleshooting

### El comando `ai` no se encuentra

**Solución 1:** Usa `uv run ai` en lugar de `ai`

**Solución 2:** Instala el CLI globalmente (ver sección de Instalación)

### Error de conexión al gateway

```bash
# Verifica que el gateway esté corriendo
uv run ai status

# Si no está corriendo, inicia el gateway
uv run uvicorn gateway.main:app --reload --app-dir apps/gateway/src
```

### Error de codificación Unicode en Windows

Si ves errores de codificación, configura UTF-8 en PowerShell:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

O usa Windows Terminal en lugar de PowerShell clásico.

## Desarrollo

### Ejecutar tests

```bash
uv run pytest tests/cli/ -v
```

### Agregar nuevos comandos

Edita `apps/cli/src/cli/main.py` y agrega nuevas funciones con el decorador `@app.command()`.

### Agregar nuevos subcomandos

Crea un nuevo `Typer` app y agrégalo al app principal:

```python
sub_app = typer.Typer(help="Descripción")
app.add_typer(sub_app, name="subcomando")
```

## Soporte

Para problemas o preguntas:
1. Revisa la documentación en `docs/`
2. Consulta los logs del gateway
3. Verifica que todos los servicios estén corriendo
