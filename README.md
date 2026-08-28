# mcp-contrataciones-py

MCP server para consultar las **contrataciones públicas de Paraguay** (DNCP, API v3, formato
[OCDS](https://standard.open-contracting.org/)) desde agentes IA (Claude, Hermes, Cursor, etc.).

- **API oficial:** https://www.contrataciones.gov.py/datos/api/v3/doc/
- **Datos:** procesos de licitación, adjudicaciones, contratos, proveedores (RUC), convocantes, catálogo de productos, parámetros y visualizaciones.
- **Sin credenciales funciona** en modo testing (15 llamadas/minuto). Con `DNCP_REQUEST_TOKEN` se usa el OAuth oficial (token renovado automáticamente cada 15 min).

## Instalación

```bash
# Desde PyPI (cuando se publique)
pip install mcp-contrataciones-py
# o con uv
uvx mcp-contrataciones-py

# Desde el repo
pip install -e .
```

## Uso con clientes MCP

**Claude Desktop / Claude Code:**

```json
{
  "mcpServers": {
    "contrataciones-py": {
      "command": "mcp-contrataciones"
    }
  }
}
```

**Hermes** (`hermes mcp add`):

```bash
hermes mcp add contrataciones-py -- python -m mcp_dncp.server
```

**Con credenciales OAuth (opcional):**

```json
{
  "mcpServers": {
    "contrataciones-py": {
      "command": "mcp-contrataciones",
      "env": { "DNCP_REQUEST_TOKEN": "tu-request-token" }
    }
  }
}
```

Para obtener el token: registrarse en https://www.contrataciones.gov.py/datos/adm/login → *Mis aplicaciones* → crear aplicación.

## Tools

| Tool | Descripción |
|---|---|
| `buscar_procesos` | Búsqueda de procesos OCDS con 11 filtros (ocid, título, convocante, RUC, categoría, modalidad, estado, fechas...) |
| `obtener_record_ocds` | Proceso completo por OCID (`ocds-03ad3f-...`) |
| `buscar_proveedores` / `obtener_proveedor` | Búsqueda por nombre/RUC/categoría/sanción; detalle por RUC |
| `buscar_convocantes` / `obtener_convocante` | Entidades contratantes por nombre/código SICP/nivel |
| `obtener_licitacion` / `obtener_contrato` / `obtener_adjudicacion` / `obtener_protesta` | Detalle por id |
| `buscar_catalogo` | Catálogo de bienes y servicios (nivel 5) |
| `obtener_categorias` / `obtener_modalidades` / `obtener_parametros` | Parámetros de referencia |
| `buscar_intenciones` | Intenciones de contratación |
| `resumen_licitaciones` / `contar_licitaciones` | Visualizaciones minimal / conteos |

## Docker

Imagen publicada en **GHCR** y **Docker Hub** (build automático vía GitHub Actions, multi-arch amd64/arm64):

```bash
docker pull ricarcya/mcp-contrataciones-py:latest        # Docker Hub
docker pull ghcr.io/ricarcya/mcp-contrataciones-py:latest # GHCR
```

**stdio** (el cliente MCP lanza el contenedor):

```json
{
  "mcpServers": {
    "contrataciones-py": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/<owner>/mcp-contrataciones-py:latest"]
    }
  }
}
```

**HTTP streamable:**

```bash
docker run --rm -p 8080:8080 -e DNCP_REQUEST_TOKEN=... \
  ghcr.io/<owner>/mcp-contrataciones-py:latest \
  python -m mcp_dncp.server --transport http --port 8080
```

Construir localmente: `docker build -t mcp-contrataciones-py .`

## Desarrollo

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

## Licencia

MIT
