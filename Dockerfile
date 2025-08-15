FROM python:3.10-slim

WORKDIR /app

# Instala uv y wheel
RUN pip install --upgrade pip && pip install uv wheel

# Copia archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instala dependencias desde pyproject.toml + uv.lock
RUN uv sync

# Copia el resto del proyecto
COPY . .

# Expone puertos usados por MCP (8008 y 8877) (puerto 8877 es para el servidor de callbacks)
EXPOSE 8008 8877

# Ejecuta el servidor MCP usando fastmcp dentro del entorno virtual de uv
CMD ["uv", "run", "fastmcp", "run", "main.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8008"]
