# AI Workstation - Guía Completa de Uso

## ¿Qué es AI Workstation?

AI Workstation es una plataforma modular de ingeniería de IA diseñada para desarrollo de software asistido por inteligencia artificial. Proporciona una interfaz unificada a múltiples proveedores de LLM con enrutamiento inteligente, gestión de contexto, ejecución de herramientas y observabilidad completa.

### ¿Para qué sirve?

- **Desarrollo asistido por IA**: Obtén ayuda contextualizada para escribir, revisar y refactorizar código
- **Automatización de tareas**: Usa herramientas para ejecutar operaciones en tu sistema de archivos, git, shell, etc.
- **Gestión de conocimiento**: Almacena y recupera información relevante entre sesiones
- **Evaluación de calidad**: Mide la calidad de las respuestas de IA con métricas objetivas
- **Observabilidad**: Monitorea el uso, costos y rendimiento de tus interacciones con IA

## Casos de Uso

### 1. Desarrollo de Software Asistido

**Escenario**: Estás trabajando en un proyecto Python y necesitas ayuda para implementar una funcionalidad.

```bash
# Iniciar sesión de trabajo
uv run ai session create --title "Implementar autenticación JWT"

# Pedir ayuda con contexto
uv run ai chat "Necesito implementar autenticación JWT en FastAPI. ¿Puedes sugerir una estructura?"

# Guardar decisiones importantes
uv run ai memory remember "Usar PyJWT para tokens, almacenar refresh tokens en Redis" --scope project --project auth-service
```

**Beneficio**: Mantienes contexto entre sesiones, acumulas conocimiento del proyecto, y tienes un historial de decisiones.

### 2. Code Review Automatizado

**Escenario**: Quieres revisar un archivo antes de hacer commit.

```bash
# Leer el archivo con herramienta
uv run ai tools exec filesystem --params '{"operation": "read", "path": "src/auth.py"}'

# Ejecutar skill de code review
uv run ai skills exec code-review --vars '{"code": "<contenido del archivo>"}'

# Guardar hallazgos
uv run ai memory remember "auth.py necesita mejor manejo de errores en línea 45" --scope project
```

**Beneficio**: Obtienes revisión de código consistente y documentas problemas para seguimiento.

### 3. Refactorización Guiada

**Escenario**: Tienes código legacy que necesita mejoras.

```bash
# Leer código existente
uv run ai tools exec filesystem --params '{"operation": "read", "path": "legacy/utils.py"}'

# Solicitar refactorización
uv run ai skills exec refactor --vars '{"code": "<código>", "goals": "Mejorar legibilidad y agregar type hints"}'

# Evaluar calidad de la sugerencia
uv run ai eval run --query "Refactorizar utils.py" --response "<sugerencia>" --metrics relevance,correctness
```

**Beneficio**: Mejoras la calidad del código con sugerencias basadas en mejores prácticas.

### 4. Generación de Tests

**Escenario**: Necesitas agregar tests a una función existente.

```bash
# Leer la función
uv run ai tools exec filesystem --params '{"operation": "read", "path": "src/calculator.py"}'

# Generar tests
uv run ai skills exec test-generation --vars '{"code": "<función>", "framework": "pytest"}'

# Escribir tests generados
uv run ai tools exec filesystem --params '{"operation": "write", "path": "tests/test_calculator.py", "content": "<tests generados>"}'
```

**Beneficio**: Aceleras la creación de tests manteniendo cobertura de código.

### 5. Gestión de Conocimiento del Proyecto

**Escenario**: Quieres documentar decisiones arquitectónicas.

```bash
# Guardar decisión
uv run ai memory remember "Decidimos usar PostgreSQL en lugar de MongoDB por las relaciones complejas" --scope project --project ecommerce

# Recuperar contexto para nuevas tareas
uv run ai memory recall "base de datos" --scope project --project ecommerce
```

**Beneficio**: Creas una base de conocimiento persistente que acelera el onboarding y la toma de decisiones.

### 6. Monitoreo de Uso y Costos

**Escenario**: Quieres saber cuánto estás gastando en APIs de LLM.

```bash
# Ver métricas
uv run ai metrics
```

**Beneficio**: Controlas costos y optimizas el uso de recursos.

## Integración con Otras Herramientas

### IDEs y Editores

#### VS Code

1. **Terminal integrada**: Usa `uv run ai` directamente en la terminal de VS Code
2. **Tasks**: Configura tasks en `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "AI: Check Status",
      "type": "shell",
      "command": "uv run ai status"
    },
    {
      "label": "AI: Chat",
      "type": "shell",
      "command": "uv run ai chat \"${input:message}\"",
      "inputs": [
        {
          "id": "message",
          "type": "promptString",
          "description": "Enter your message"
        }
      ]
    }
  ]
}
```

#### Cursor

Cursor ya tiene integración con IA, pero puedes usar AI Workstation para:
- Gestión de sesiones persistentes
- Herramientas adicionales (git, filesystem)
- Métricas y observabilidad
- Memoria compartida entre proyectos

#### JetBrains (PyCharm, WebStorm)

1. **External Tools**: Configura en Settings > Tools > External Tools
2. **Terminal**: Usa directamente en la terminal integrada

### Git Hooks

#### Pre-commit Hook

Crea `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Guardar contexto antes de commit
uv run ai memory remember "Commit: $(git log -1 --pretty=%B)" --scope project

# Opcional: Code review automático
uv run ai tools exec git --params '{"command": "diff", "args": ["--cached"]}' | \
  uv run ai skills exec code-review --vars '{"code": "<diff>"}'
```

#### Post-commit Hook

Crea `.git/hooks/post-commit`:

```bash
#!/bin/bash
# Registrar métricas de commit
echo "Commit realizado en $(date)" >> .ai-workstation/commits.log
```

### CI/CD Pipelines

#### GitHub Actions

```yaml
name: AI-Assisted Development
on: [push, pull_request]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup AI Workstation
        run: |
          pip install uv
          uv sync --all-packages
      
      - name: AI Code Review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          # Obtener diff
          git diff main...HEAD > diff.txt
          
          # Ejecutar review
          uv run ai skills exec code-review --vars '{"code": "$(cat diff.txt)"}'
```

#### GitLab CI

```yaml
ai_review:
  stage: test
  image: python:3.11
  script:
    - pip install uv
    - uv sync --all-packages
    - uv run ai skills exec code-review --vars '{"code": "'$CI_MERGE_REQUEST_DIFF"'"}'
  only:
    - merge_requests
```

### APIs REST

AI Workstation expone una API REST completa que puedes integrar con cualquier aplicación:

```python
import httpx

# Chat
response = httpx.post(
    "http://localhost:8000/chat",
    json={
        "messages": [{"role": "user", "content": "Hello"}],
        "session_id": "my-session"
    }
)

# Ejecutar herramienta
response = httpx.post(
    "http://localhost:8000/tools/filesystem/execute",
    json={
        "params": {
            "operation": "read",
            "path": "/path/to/file"
        }
    }
)

# Guardar memoria
response = httpx.post(
    "http://localhost:8000/memory/remember",
    params={
        "content": "Important decision",
        "scope": "project",
        "project_id": "my-project"
    }
)
```

### MCP (Model Context Protocol)

AI Workstation implementa el protocolo MCP, compatible con herramientas como:

- **Claude Desktop**: Configura como servidor MCP
- **Cline**: Integración directa
- **Continue**: Usa como backend

Ejemplo de configuración para Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ai-workstation": {
      "command": "uv",
      "args": ["run", "ai"],
      "env": {
        "GATEWAY_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Flujos de Trabajo Recomendados

### Flujo 1: Desarrollo Diario

```bash
# 1. Iniciar el día
uv run ai status  # Verificar que todo está funcionando

# 2. Crear sesión para la tarea actual
uv run ai session create --title "Implementar feature X"

# 3. Trabajar con contexto
uv run ai chat "Estoy trabajando en feature X. ¿Qué consideraciones debo tener?"

# 4. Guardar progreso
uv run ai memory remember "Feature X: completado 50%, falta testing" --scope session

# 5. Al final del día, revisar métricas
uv run ai metrics
```

### Flujo 2: Code Review en Equipo

```bash
# 1. Obtener diff del PR
uv run ai tools exec git --params '{"command": "diff", "args": ["main...feature-branch"]}'

# 2. Ejecutar review
uv run ai skills exec code-review --vars '{"code": "<diff>"}'

# 3. Guardar hallazgos
uv run ai memory remember "PR #123: problemas de performance en línea 45" --scope project

# 4. Generar resumen para el equipo
uv run ai chat "Resume los hallazgos del code review del PR #123"
```

### Flujo 3: Refactorización Segura

```bash
# 1. Identificar código a refactorizar
uv run ai tools exec filesystem --params '{"operation": "read", "path": "src/legacy.py"}'

# 2. Solicitar análisis
uv run ai chat "¿Qué problemas ves en este código y cómo lo mejorarías?"

# 3. Ejecutar refactorización
uv run ai skills exec refactor --vars '{"code": "<código>", "goals": "Mejorar legibilidad"}'

# 4. Evaluar calidad
uv run ai eval run --query "Refactorizar legacy.py" --response "<sugerencia>" --metrics correctness,relevance

# 5. Generar tests
uv run ai skills exec test-generation --vars '{"code": "<código refactorizado>"}'
```

### Flujo 4: Onboarding de Nuevos Desarrolladores

```bash
# 1. Crear sesión de onboarding
uv run ai session create --title "Onboarding - Nuevo desarrollador"

# 2. Preguntar sobre el proyecto
uv run ai chat "Explícame la arquitectura de este proyecto"

# 3. Recuperar conocimiento acumulado
uv run ai memory recall "arquitectura" --scope project --limit 10

# 4. Hacer preguntas específicas
uv run ai chat "¿Cómo funciona el sistema de autenticación?"

# 5. Guardar aprendizajes
uv run ai memory remember "Aprendí que el sistema usa JWT con refresh tokens" --scope session
```

## Beneficios Concretos

### Para Desarrolladores Individuales

1. **Productividad**: Reduce tiempo en tareas repetitivas (code review, tests, documentación)
2. **Contexto persistente**: No pierdes el hilo entre sesiones
3. **Calidad de código**: Obtienes sugerencias basadas en mejores prácticas
4. **Aprendizaje continuo**: Acumulas conocimiento del proyecto
5. **Métricas personales**: Sabes cuánto usas IA y en qué

### Para Equipos

1. **Consistencia**: Code review estandarizado
2. **Documentación automática**: Decisiones y contexto se guardan automáticamente
3. **Onboarding acelerado**: Nuevos miembros acceden a conocimiento acumulado
4. **Control de costos**: Métricas de uso por equipo/proyecto
5. **Mejores prácticas**: Skills que encapsulan patrones del equipo

### Para Organizaciones

1. **ROI medible**: Métricas de productividad y calidad
2. **Gobernanza**: Control sobre qué modelos se usan y cuánto cuestan
3. **Seguridad**: Sandboxing de herramientas, logs de auditoría
4. **Escalabilidad**: Arquitectura modular que crece con la organización
5. **Vendor independence**: Soporte para múltiples proveedores de LLM

## Implementación Paso a Paso

### Paso 1: Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd ai-workstation

# Instalar dependencias
uv sync --all-packages

# Iniciar infraestructura
docker compose -f infrastructure/compose/docker-compose.yml up -d

# Verificar instalación
uv run ai status
```

### Paso 2: Configuración Inicial

1. **Configurar API keys**:

```bash
# Crear archivo .env
cp infrastructure/compose/.env.example infrastructure/compose/.env

# Editar .env con tus API keys
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

2. **Configurar modelo por defecto**:

```bash
# En .env
DEFAULT_MODEL=gpt-4
```

3. **Iniciar gateway**:

```bash
uv run uvicorn gateway.main:app --reload --app-dir apps/gateway/src
```

### Paso 3: Primer Uso

```bash
# Verificar estado
uv run ai status

# Crear primera sesión
uv run ai session create --title "Mi primera sesión"

# Hacer una pregunta
uv run ai chat "¿Qué puedes hacer por mí?"

# Explorar herramientas
uv run ai tools list

# Explorar skills
uv run ai skills list
```

### Paso 4: Integración con tu Flujo

1. **Agregar alias a tu shell**:

```bash
# En ~/.bashrc o ~/.zshrc
alias ai="uv run ai"
alias aic="uv run ai chat"
alias ais="uv run ai session"
```

2. **Configurar en tu IDE** (ver sección de integración)

3. **Crear scripts personalizados**:

```bash
#!/bin/bash
# scripts/ai-review.sh
uv run ai tools exec git --params '{"command": "diff", "args": ["HEAD~1"]}' | \
  uv run ai skills exec code-review --vars '{"code": "<diff>"}'
```

### Paso 5: Producción

Para despliegue en producción:

```bash
# Usar configuración de producción
docker compose -f infrastructure/compose/docker-compose.prod.yml up -d

# O usar script de despliegue
./infrastructure/deployment/deploy.sh deploy
```

## Preguntas Frecuentes

### ¿Necesito pagar por APIs de LLM?

Sí, necesitas al menos una API key de un proveedor de LLM (OpenAI, Anthropic, Google, etc.). AI Workstation usa LiteLLM, que soporta más de 100 proveedores.

### ¿Puedo usar modelos locales?

Sí, AI Workstation soporta Ollama y otros proveedores locales. Configura el proveedor en el router.

### ¿Es seguro usar en producción?

Sí, con las siguientes consideraciones:
- Cambia passwords por defecto en `.env`
- Usa HTTPS con reverse proxy
- Configura autenticación en Grafana
- Revisa logs de auditoría regularmente

### ¿Cuánto cuesta mantener?

Los costos principales son:
- APIs de LLM (variable según uso)
- Infraestructura (PostgreSQL, Redis, Qdrant)
- Tiempo de mantenimiento (mínimo con arquitectura modular)

### ¿Puedo contribuir?

¡Sí! Revisa la sección de Contributing en `AGENTS.md`.

### ¿Hay soporte comercial?

Actualmente es un proyecto de código abierto. Para soporte comercial, contacta a los mantenedores.

## Recursos Adicionales

- [Documentación de Arquitectura](architecture/ARCHITECTURE.md)
- [Guía del CLI](../apps/cli/README.md)
- [Architecture Decision Records](adr/)
- [Roadmap de Fases](roadmap/)

## Soporte y Comunidad

- **Issues**: Reporta bugs o solicita features en el repositorio
- **Discusiones**: Participa en discusiones sobre el proyecto
- **Contribuciones**: Pull requests son bienvenidos

---

**Última actualización**: Julio 2025  
**Versión**: 1.0.0
