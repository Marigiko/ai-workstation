# Infrastructure Monitoring

Este directorio contiene las configuraciones de monitoreo para AI Workstation.

## Estructura

```
monitoring/
├── prometheus.yml              # Configuración de Prometheus
├── rules/
│   └── alerts.yml             # Reglas de alerta
└── grafana/
    ├── provisioning/
    │   ├── datasources/       # Data sources de Grafana
    │   └── dashboards/        # Configuración de dashboards
    └── dashboards/
        └── overview.json      # Dashboard principal
```

## Componentes

### Prometheus

Prometheus recolecta métricas de todos los servicios:

- **Gateway**: Métricas de requests, latencia, errores
- **PostgreSQL**: Métricas de base de datos (requiere postgres_exporter)
- **Redis**: Métricas de cache (requiere redis_exporter)
- **Node**: Métricas del sistema (requiere node_exporter)

### Alertas

Las alertas están configuradas en `rules/alerts.yml`:

- **GatewayDown**: Gateway no responde
- **HighRequestLatency**: Latencia > 2s (p95)
- **HighErrorRate**: Error rate > 5%
- **HighCpuUsage**: CPU > 80%
- **HighMemoryUsage**: Memoria > 85%
- **DiskSpaceLow**: Disco < 15%
- **LLMAPIErrors**: Errores en LLM API
- **HighTokenUsage**: Uso de tokens > 10k/hora

### Grafana

Grafana proporciona dashboards visuales:

- **Overview**: Métricas generales del sistema
- **Gateway**: Detalles del gateway
- **LLM**: Uso de modelos y tokens

## Acceso

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
  - Usuario: admin
  - Password: admin (cambiar en producción)

## Configuración

### Variables de Entorno

```bash
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

### Agregar Nuevas Métricas

1. Instrumentar el código con métricas Prometheus
2. Exponer endpoint `/metrics` en el servicio
3. Agregar job en `prometheus.yml`
4. Crear panel en Grafana

### Agregar Nuevas Alertas

1. Editar `rules/alerts.yml`
2. Definir expresión PromQL
3. Configurar severidad y anotaciones
4. Recargar Prometheus: `docker exec ai-workstation-prometheus kill -HUP 1`

## Exporters Adicionales

Para monitoreo completo, agregar estos exporters al docker-compose:

### PostgreSQL Exporter

```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://ai_workstation:ai_workstation_dev@postgres:5432/ai_workstation?sslmode=disable"
  ports:
    - "9187:9187"
```

### Redis Exporter

```yaml
redis-exporter:
  image: oliver006/redis_exporter
  environment:
    REDIS_ADDR: "redis://redis:6379"
  ports:
    - "9121:9121"
```

### Node Exporter

```yaml
node-exporter:
  image: prom/node-exporter
  ports:
    - "9100:9100"
```

## Troubleshooting

### Prometheus no scrapea métricas

1. Verificar que el servicio expone `/metrics`
2. Verificar conectividad de red entre containers
3. Revisar logs: `docker logs ai-workstation-prometheus`

### Grafana no muestra datos

1. Verificar que Prometheus está funcionando
2. Verificar datasource en Grafana
3. Revisar queries en Dev Tools (Ctrl+Alt+D)

### Alertas no se disparan

1. Verificar que las reglas están cargadas: `http://localhost:9090/rules`
2. Verificar expresión PromQL
3. Revisar logs de Prometheus
