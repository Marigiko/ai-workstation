# Infrastructure Docker

Este directorio contiene los Dockerfiles para construir las imágenes de AI Workstation.

## Estructura

```
docker/
├── Dockerfile.gateway    # Dockerfile para el Gateway
└── Dockerfile.cli        # Dockerfile para el CLI
```

## Dockerfiles

### Gateway

Construye la imagen del Gateway de AI Workstation.

**Características:**
- Multi-stage build para reducir tamaño final
- Python 3.11 slim como base
- Usuario no-root por seguridad
- Health check integrado
- Optimizado para producción

**Construir:**
```bash
docker build -f Dockerfile.gateway -t ai-workstation-gateway ../..
```

**Ejecutar:**
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e REDIS_URL=redis://redis:6379 \
  -e QDRANT_URL=http://qdrant:6333 \
  ai-workstation-gateway
```

### CLI

Construye la imagen del CLI de AI Workstation.

**Características:**
- Multi-stage build
- Entry point configurado como `ai`
- Usuario no-root

**Construir:**
```bash
docker build -f Dockerfile.cli -t ai-workstation-cli ../..
```

**Ejecutar:**
```bash
docker run -e GATEWAY_URL=http://gateway:8000 ai-workstation-cli status
```

## Optimizaciones

### Multi-stage Build

Usamos multi-stage builds para:
- Reducir tamaño final de la imagen
- Separar dependencias de build y runtime
- Mejorar seguridad (no incluir herramientas de build)

### Capas de Cache

Orden de las capas para maximizar cache:
1. Dependencias del sistema (rara vez cambian)
2. Dependencias de Python (cambian con pyproject.toml)
3. Código fuente (cambia frecuentemente)

### Seguridad

- Usuario no-root (`appuser`)
- No incluir archivos innecesarios
- Usar imágenes oficiales como base
- Escanear vulnerabilidades regularmente

## Variables de Entorno

### Gateway

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379

# Qdrant
QDRANT_URL=http://host:6333

# Modelos
DEFAULT_MODEL=gpt-4
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Aplicación
LOG_LEVEL=INFO
DEBUG=false
```

### CLI

```bash
# Gateway
GATEWAY_URL=http://host:8000
```

## Registry

Para publicar las imágenes en un registry:

```bash
# Login
docker login registry.example.com

# Tag
docker tag ai-workstation-gateway registry.example.com/ai-workstation-gateway:v1.0.0
docker tag ai-workstation-cli registry.example.com/ai-workstation-cli:v1.0.0

# Push
docker push registry.example.com/ai-workstation-gateway:v1.0.0
docker push registry.example.com/ai-workstation-cli:v1.0.0
```

## Debugging

### Inspeccionar imagen

```bash
docker run --rm -it ai-workstation-gateway /bin/bash
```

### Ver capas

```bash
docker history ai-workstation-gateway
```

### Tamaño de imagen

```bash
docker images ai-workstation-gateway
```

### Logs

```bash
docker logs <container-id>
```

## Troubleshooting

### Build falla

1. Verificar que todos los `pyproject.toml` existen
2. Verificar conectividad a internet (para descargar dependencias)
3. Revisar logs de build completo
4. Verificar versión de Docker

### Imagen muy grande

1. Verificar que se usa multi-stage build
2. Revisar `.dockerignore`
3. Eliminar dependencias innecesarias
4. Usar imágenes slim como base

### Container no inicia

1. Verificar variables de entorno
2. Verificar conectividad a servicios externos
3. Revisar logs del container
4. Verificar health check

## Mejoras Futuras

- [ ] Agregar soporte para ARM64
- [ ] Implementar image signing
- [ ] Agregar labels OCI
- [ ] Implementar SBOM generation
- [ ] Agregar tests de seguridad automatizados
