# PLAN — MCP Server API DNCP Paraguay

**Objetivo:** MCP server que expone los datos de contrataciones públicas de Paraguay (DNCP, API v3, formato OCDS) a agentes IA (Claude, Hermes, Cursor, etc.), con despliegue Docker automatizado desde GitHub (GHCR).

**Referencia:** investigación completa en `~/dncp-mcp-research/INFORME-INVESTIGACION.md` (spec, endpoints, herramientas existentes).

---

## Fase 0 — Investigación (✅ COMPLETADA)

- API v3 verificada en vivo: base `https://www.contrataciones.gov.py/datos/api/v3/doc/`, 30 endpoints, spec `swagger.json` descargada.
- No existe MCP standalone para DNCP → hueco confirmado. Referencias: SIGECOP (auth Python), secop-mcp-server (estructura MCP Python), mcp-india-tenders (arquitectura OCDS).

## Fase 1 — Scaffold del MCP server (PENDIENTE)

- Lenguaje: **Python** (confirmar) con SDK `mcp` (o `fastmcp`).
- Estructura:
  ```
  src/mcp_dncp/
    ├── __init__.py
    ├── server.py        # definición de tools MCP
    ├── client.py        # cliente HTTP de la API DNCP v3 (base URL, parámetros, paginación)
    ├── auth.py          # OAuth: request_token → access token (cache + refresh cada 15 min)
    └── datasets.py      # mapeo de endpoints → tools (patrón secop-mcp-server)
  ```
- Tools propuestas (mapeo 1:1 a la API):
  | Tool | Endpoint |
  |---|---|
  | `buscar_procesos` | `/search/processes` (28 filtros OCDS) |
  | `obtener_record_ocds` | `/ocds/record/{ocid}` |
  | `buscar_proveedores` / `obtener_proveedor` | `/search/suppliers`, `/suppliers/{ruc}` |
  | `buscar_convocantes` / `obtener_convocante` | `/search/procuringEntities`, `/procuringEntities/{id}` |
  | `obtener_licitacion` / `obtener_contrato` / `obtener_adjudicacion` | `/tender/{id}`, `/contracts/{id}`, `/awards/{id}` |
  | `buscar_catalogo` / `obtener_producto` | `/search/classification`, `/itemClassification/n4|n5` |
  | `obtener_parametros` (categorías, modalidades, dominios) | `/parameters/*` |
  | `buscar_intenciones` | `/search/procurementIntentions` |
  | `buscar_protestas` | `/complaints/{id}` |
  | `resumen_tenders` / `resumen_contratos_convocante` | `/visualizations/minimal/*` |
- Auth opcional: sin token → modo testing (15 calls/min); con env `DNCP_REQUEST_TOKEN` → OAuth real.
- Tests: pytest (mock de respuestas), ruff.

## Fase 2 — Docker (✅ ARCHIVOS GENERADOS, validar con código real)

- `Dockerfile` multi-stage (builder wheels + runtime slim, usuario no-root, `PYTHONUNBUFFERED`).
- Transporte: stdio por defecto (`ENTRYPOINT mcp run`); alternativa HTTP streamable (EXPOSE 8080) documentada.
- `.dockerignore` + `docker-compose.yml` de ejemplo (env `DNCP_REQUEST_TOKEN`).
- Validar local: `docker build -t mcp-dncp:test .`

## Fase 3 — GitHub + CI/CD automatizado (PENDIENTE de decisiones)

1. Crear repo (gh) → push del código.
2. `.github/workflows/ci.yml` — lint + tests en PR/main.
3. `.github/workflows/docker-build.yml` — buildx multi-arch (amd64/arm64) + push a **GHCR** `ghcr.io/<owner>/<repo>`:
   - push a `main` → tag `latest`
   - tag `v*` (semver) → tags `v1.2.3`, `v1`, `1.2`
   - `workflow_dispatch` manual con tag opcional
   - cache GHA + provenance/SBOM (buildkit)
   - sin secrets extra: `GITHUB_TOKEN` basta para GHCR
4. (Opcional) protección de `main` + release notes con `gh release create`.

## Fase 4 — Publicación y uso

- README con: instalación (`pip install` / `uvx`), config en Claude Desktop/Hermes (stdio y/o HTTP), uso de la imagen Docker.
- Registrar en directorios MCP (mcpmarket, glama, mcp.so) — hueco de "Paraguay DNCP" ya indexado por Pipeworx.
- Registrar en Hermes local (skill `hermes-custom-mcp`) para usarlo desde esta máquina.

---

## Decisiones pendientes
- [ ] Stack: Python (recomendado) vs TypeScript
- [ ] Nombre del repo + visibilidad (público/privado) + owner (personal / org Easy)
- [ ] Autenticar `gh` (device flow) para crear repo y push
