# Aveonline MCP Server

Servidor MCP de AveOnline construido con `FastMCP 2.0`.

---

## 🧱 Requisitos

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) para gestión de dependencias
- Docker (opcional para despliegue en contenedor)

---

## .env
[Credenciales de Google](https://console.cloud.google.com/apis/credentials) > Clientes de OAuth 2.0 > Tipo: `Escritorio`
```env
CALLBACK_SERVER_PORT=8870

# OAuth Configuration
REDIRECT_URI="http://localhost"
CLIENT_ID="xxxxxx-ipsxxxxxx.apps.googleusercontent.com"
CLIENT_SECRET="GOCSPX-xxxxxxxxxx"
CALLBACK_SERVER_HOST="0.0.0.0"


DOCKER_ENVIRONMENT=1
LOG_LEVEL="info"

SECRET_KEY=""
SECRET_IV=""
CRYPTER_METHOD="AES"

# Redis Configuration
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
# REDIS_HOST=localhost # Para desarrollo local
REDIS_HOST=redis

# Session Configuration
SESSION_TIMEOUT=3600
SESSION_SECRET=mi_clave

```

## 🚀 Instalación local

### 1. Instalar dependencias

```bash
uv sync
# o para reinstalar completamente
uv sync --reinstall
```

### 2. Activar entorno virtual

```bash
.venv\Scripts\activate  # En Windows
# o
source .venv/bin/activate  # En Linux/macOS
```

### 3. Ejecutar el servidor MCP

```bash
fastmcp run main.py --transport streamable-http
```

Accede a: [http://localhost:8008/mcp/](http://localhost:8008/mcp/)

---

## 🐳 Despliegue con Docker

### Opción 1: Docker Compose (recomendado)

```bash
docker-compose up -d
```

> Asegúrate de tener un archivo `.env` si el `docker-compose.yml` lo requiere.

---

### Opción 2: Manual (Build + Run)

```bash
docker build -t mcp-server-ave .
docker run -p 8008:8008 -p 8877:8877 --name aveonline-mcp-server mcp-server-ave
```

---

## 🛠️ Problemas comunes

- Si algo falla durante la instalación local:
  - Elimina la carpeta `.venv`
  - Ejecuta nuevamente `uv sync`

---

## 📚 Recursos

- 🌐 [FastMCP Docs](https://gofastmcp.com/getting-started/welcome) - SDK para crear servidores MCP con FastAPI
- 🐍 [Python SDK for MCP](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#installation) - SDK oficial para Python

---

## 🧩 Información técnica

- MCP Transport: `Streamable-HTTP`
- Puerto por defecto: `8008`
- Endpoint: `/mcp/`
- Se requiere el `CLIENT_ID` y `CLIENT_SECRET` para la OAuth
- Puerto Callback (OAuth): `8877`

---

## Redis
# Ver logs de Redis
docker-compose logs -f redis

# Conectarse a Redis CLI
docker exec -it aveonline-redis redis-cli

# Monitorear comandos Redis
docker exec -it aveonline-redis redis-cli MONITOR

# Verificar sesiones activas
docker exec -it aveonline-redis redis-cli KEYS "*session:*"

# Limpiar todas las sesiones
docker exec -it aveonline-redis redis-cli FLUSHDB