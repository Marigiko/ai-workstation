# Infrastructure Deployment

Este directorio contiene scripts y configuraciones para el despliegue de AI Workstation.

## Estructura

```
deployment/
├── deploy.sh          # Script de despliegue (Linux/Mac)
├── deploy.ps1         # Script de despliegue (Windows)
├── backup.sh          # Script de backup
└── health-check.sh    # Script de verificación de salud
```

## Scripts

### Deploy

Despliega la plataforma completa:

**Linux/Mac:**
```bash
./deploy.sh deploy
```

**Windows:**
```powershell
.\deploy.ps1 deploy
```

**Comandos disponibles:**
- `deploy`: Despliega todos los servicios
- `stop`: Detiene todos los servicios
- `restart`: Reinicia todos los servicios
- `status`: Muestra el estado de los servicios
- `logs [service]`: Muestra logs (opcionalmente de un servicio específico)

### Backup

Crea backups de las bases de datos:

```bash
./backup.sh all        # Backup completo
./backup.sh postgres   # Solo PostgreSQL
./backup.sh qdrant     # Solo Qdrant
./backup.sh redis      # Solo Redis
./backup.sh cleanup    # Limpiar backups antiguos
```

**Variables de entorno:**
```bash
BACKUP_DIR=/path/to/backups
BACKUP_RETENTION_DAYS=7
```

### Health Check

Verifica el estado de todos los servicios:

```bash
./health-check.sh
```

## Despliegue Manual

Si prefieres desplegar manualmente:

### 1. Configurar Variables de Entorno

```bash
cp ../compose/.env.example ../compose/.env
# Editar .env con tus valores
```

### 2. Construir Imágenes

```bash
docker compose -f ../compose/docker-compose.prod.yml build
```

### 3. Iniciar Servicios

```bash
docker compose -f ../compose/docker-compose.prod.yml up -d
```

### 4. Verificar Salud

```bash
curl http://localhost:8000/health
```

### 5. Ejecutar Migraciones

```bash
docker compose -f ../compose/docker-compose.prod.yml exec gateway alembic upgrade head
```

## Producción

### Consideraciones de Seguridad

1. **Cambiar passwords por defecto** en `.env`
2. **Usar HTTPS** con un reverse proxy (nginx, traefik)
3. **Configurar firewall** para limitar acceso
4. **Habilitar autenticación** en Grafana
5. **Rotar API keys** regularmente

### Reverse Proxy (Nginx)

Ejemplo de configuración para nginx:

```nginx
upstream gateway {
    server gateway:8000;
}

upstream grafana {
    server grafana:3000;
}

server {
    listen 443 ssl http2;
    server_name ai-workstation.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /grafana/ {
        proxy_pass http://grafana/;
        proxy_set_header Host $host;
    }
}
```

### Escalabilidad

Para escalar horizontalmente:

1. **Gateway**: Stateless, puede escalar horizontalmente
2. **PostgreSQL**: Usar replicas de lectura
3. **Redis**: Usar Redis Cluster
4. **Qdrant**: Usar Qdrant cluster mode

### Monitoreo

Ver `../monitoring/README.md` para configuración de monitoreo.

## Troubleshooting

### Servicios no inician

1. Verificar logs: `docker compose logs [service]`
2. Verificar puertos disponibles
3. Verificar espacio en disco
4. Verificar permisos de archivos

### Base de datos no conecta

1. Verificar que PostgreSQL está healthy
2. Verificar credenciales en `.env`
3. Verificar conectividad de red
4. Revisar logs de PostgreSQL

### Migraciones fallan

1. Verificar estado actual: `alembic current`
2. Revisar logs de migraciones
3. Verificar schema de base de datos
4. Ejecutar manualmente si es necesario

### Backups fallan

1. Verificar permisos de escritura en `BACKUP_DIR`
2. Verificar espacio en disco
3. Verificar que los containers están running
4. Revisar logs del script

## CI/CD

Ejemplo de pipeline para GitHub Actions:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy
        run: |
          ./infrastructure/deployment/deploy.sh deploy
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Soporte

Para problemas o preguntas:
1. Revisar logs de los servicios
2. Consultar documentación en `docs/`
3. Verificar health check
4. Revisar métricas en Grafana
