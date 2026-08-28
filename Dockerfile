# syntax=docker/dockerfile:1

# ---------- BUILDER ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Dependencias de build (si se usan wheels nativos, p. ej. httpx/anyio son puros)
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# ---------- RUNTIME ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Usuario no-root
RUN addgroup --system mcp && adduser --system --ingroup mcp mcp

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

USER mcp

# Transporte por defecto: stdio (MCP). Para streamable HTTP:
#   docker run ... mcp-contrataciones-py python -m mcp_dncp.server --transport http --port 8080
EXPOSE 8080

ENTRYPOINT ["python", "-m", "mcp_dncp.server"]
