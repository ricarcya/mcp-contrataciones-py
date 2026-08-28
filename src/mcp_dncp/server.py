"""MCP server: contrataciones públicas de Paraguay (DNCP API v3).

Uso:
    mcp-contrataciones                  # transporte stdio (default)
    mcp-contrataciones --transport http --port 8080   # streamable HTTP
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from functools import wraps
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import DncpClient, DncpError

mcp = FastMCP(
    "mcp-contrataciones-py",
    instructions=(
        "Datos de contrataciones públicas de Paraguay (DNCP, API v3, formato OCDS). "
        "Fuente oficial: https://www.contrataciones.gov.py/datos. "
        "Los OCID tienen el formato ocds-03ad3f-<nro>; un proveedor se identifica por su RUC; "
        "una convocante por su código SICP. Sin token DNCP_REQUEST_TOKEN se opera en modo "
        "testing (15 llamadas/minuto)."
    ),
)

_client: DncpClient | None = None


def get_client() -> DncpClient:
    global _client
    if _client is None:
        _client = DncpClient()
    return _client


def _handle_errors(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Convierte errores de la API en mensajes claros para el LLM."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except DncpError as exc:
            raise ValueError(f"Error consultando la API DNCP: {exc}") from exc
        except Exception as exc:
            raise ValueError(f"Error inesperado en {fn.__name__}: {exc}") from exc

    return wrapper


# ---------------------------------------------------------------------- #
# Detalle por id
# ---------------------------------------------------------------------- #
@mcp.tool()
@_handle_errors
def obtener_record_ocds(ocid: str) -> dict[str, Any]:
    """Obtiene el proceso de contratación completo (record OCDS) dado su OCID, p. ej. 'ocds-03ad3f-487119-1'."""
    return get_client().get_record(ocid)


@mcp.tool()
@_handle_errors
def obtener_licitacion(id_licitacion: str) -> dict[str, Any]:
    """Obtiene los datos de una licitación (llamado) dado su id numérico."""
    return get_client().get_tender(id_licitacion)


@mcp.tool()
@_handle_errors
def obtener_contrato(id_contrato: str) -> dict[str, Any]:
    """Obtiene los datos de un contrato firmado dado su código de contratación."""
    return get_client().get_contract(id_contrato)


@mcp.tool()
@_handle_errors
def obtener_adjudicacion(id_adjudicacion: str) -> dict[str, Any]:
    """Obtiene los datos de una adjudicación (proveedor adjudicado) dado su id."""
    return get_client().get_award(id_adjudicacion)


@mcp.tool()
@_handle_errors
def obtener_protesta(id_protesta: str) -> dict[str, Any]:
    """Obtiene los datos de una protesta/denuncia dado su id."""
    return get_client().get_complaint(id_protesta)


@mcp.tool()
@_handle_errors
def obtener_proveedor(ruc: str) -> dict[str, Any]:
    """Obtiene los datos de un proveedor del Estado dado su RUC."""
    return get_client().get_supplier(ruc)


@mcp.tool()
@_handle_errors
def obtener_convocante(id_convocante: str) -> dict[str, Any]:
    """Obtiene los datos de una entidad convocante dado su código SICP."""
    return get_client().get_procuring_entity(id_convocante)


# ---------------------------------------------------------------------- #
# Búsquedas
# ---------------------------------------------------------------------- #
@mcp.tool()
@_handle_errors
def buscar_procesos(
    ocid: str | None = None,
    titulo: str | None = None,
    convocante: str | None = None,
    codigo_convocante: str | None = None,
    ruc_proveedor: str | None = None,
    categoria: str | None = None,
    modalidad: str | None = None,
    estado: str | None = None,
    tipo_fecha: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    pagina: int = 1,
    items_por_pagina: int = 10,
) -> dict[str, Any]:
    """Busca procesos de contratación pública con filtros del estándar OCDS.

    Se requiere al menos un filtro. Fechas en formato YYYY-MM-DD. tipo_fecha puede ser
    'entrega_ofertas', 'adjudicacion', 'publicacion' u otros valores del parámetro
    'tipo_fecha' de la API. Devuelve record package OCDS con paginación.
    """
    filters: dict[str, Any] = {
        "ocid": ocid,
        "tender.title": titulo,
        "tender.procuringEntity.name": convocante,
        "parties.identifier.id": codigo_convocante,
        "awards.suppliers.id": ruc_proveedor,
        "tender.items.classification.id": categoria,
        "tender.procurementMethodDetails": modalidad,
        "tender.statusDetails": estado,
        "tipo_fecha": tipo_fecha,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "page": pagina,
        "items_per_page": items_por_pagina,
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    if not any(k.startswith(("ocid", "tender", "parties", "awards", "tipo_fecha", "fecha_")) for k in filters):
        raise ValueError(
            "Se requiere al menos un filtro (ocid, titulo, convocante, ruc_proveedor, "
            "categoria, modalidad, estado, o rango de fechas con tipo_fecha)."
        )
    return get_client().search_processes(**filters)


@mcp.tool()
@_handle_errors
def buscar_proveedores(
    nombre: str | None = None,
    ruc: str | None = None,
    categoria: str | None = None,
    sancionado: bool | None = None,
    pagina: int = 1,
    items_por_pagina: int = 10,
) -> dict[str, Any]:
    """Busca proveedores del Estado por nombre, RUC, categoría o estado de sanción."""
    filters: dict[str, Any] = {
        "name": nombre,
        "identifier.id": ruc,
        "details.categories.id": categoria,
        "details.sanctions.type": "sancionado" if sancionado else None,
        "page": pagina,
        "items_per_page": items_por_pagina,
    }
    return get_client().search_suppliers(**{k: v for k, v in filters.items() if v is not None})


@mcp.tool()
@_handle_errors
def buscar_convocantes(
    nombre: str | None = None,
    codigo_sicp: str | None = None,
    nivel: str | None = None,
    tipo_entidad: str | None = None,
    pagina: int = 1,
    items_por_pagina: int = 10,
) -> dict[str, Any]:
    """Busca entidades convocantes (instituciones que contratan) por nombre, código SICP, nivel o tipo."""
    filters: dict[str, Any] = {
        "name": nombre,
        "identifier.id": codigo_sicp,
        "details.level": nivel,
        "details.entityType": tipo_entidad,
        "page": pagina,
        "items_per_page": items_por_pagina,
    }
    return get_client().search_procuring_entities(**{k: v for k, v in filters.items() if v is not None})


@mcp.tool()
@_handle_errors
def buscar_catalogo(
    nombre: str | None = None,
    codigo: str | None = None,
    categoria: str | None = None,
    pagina: int = 1,
    items_por_pagina: int = 10,
) -> dict[str, Any]:
    """Busca productos del catálogo de bienes y servicios (nivel 5) por nombre o código."""
    filters: dict[str, Any] = {
        "name": nombre,
        "id": codigo,
        "categories.id": categoria,
        "page": pagina,
        "items_per_page": items_por_pagina,
    }
    return get_client().search_classification(**{k: v for k, v in filters.items() if v is not None})


@mcp.tool()
@_handle_errors
def buscar_intenciones(
    convocante: str | None = None,
    codigo_convocante: str | None = None,
    id_intencion: str | None = None,
    estado: str | None = None,
    pagina: int = 1,
    items_por_pagina: int = 10,
) -> dict[str, Any]:
    """Busca intenciones de contratación (excepciones con difusión posterior)."""
    filters: dict[str, Any] = {
        "procuringEntity.name": convocante,
        "procuringEntity.id": codigo_convocante,
        "id": id_intencion,
        "relatedProcesses.status": estado,
        "page": pagina,
        "items_per_page": items_por_pagina,
    }
    return get_client().search_procurement_intentions(
        **{k: v for k, v in filters.items() if v is not None}
    )


# ---------------------------------------------------------------------- #
# Parámetros de referencia
# ---------------------------------------------------------------------- #
@mcp.tool()
@_handle_errors
def obtener_parametros(dominio: str | None = None) -> dict[str, Any]:
    """Lista los parámetros/dominios de la API (aseguradoras autorizadas, etc.). Opcional: filtrar por dominio."""
    return get_client().get_parameters(**({"domain": dominio} if dominio else {}))


@mcp.tool()
@_handle_errors
def obtener_categorias() -> dict[str, Any]:
    """Lista las categorías de contratación (bienes, servicios, obras, consultorías...)."""
    return get_client().get_procurement_categories()


@mcp.tool()
@_handle_errors
def obtener_modalidades() -> dict[str, Any]:
    """Lista las modalidades de contratación (licitación pública, contratación directa, etc.)."""
    return get_client().get_procurement_methods()


# ---------------------------------------------------------------------- #
# Visualizaciones
# ---------------------------------------------------------------------- #
@mcp.tool()
@_handle_errors
def resumen_licitaciones(
    categoria: str | None = None,
    modalidad: str | None = None,
    comprador: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
) -> dict[str, Any]:
    """Resumen minimal de licitaciones, opcionalmente filtrado por categoría, modalidad, comprador o rango de fechas."""
    params: dict[str, Any] = {
        "mainProcurementCategoryDetails": categoria,
        "procurementMethodDetails": modalidad,
        "buyer": comprador,
        "tenderPeriod_from": desde,
        "tenderPeriod_until": hasta,
    }
    return get_client().minimal_tenders(**{k: v for k, v in params.items() if v is not None})


@mcp.tool()
@_handle_errors
def contar_licitaciones(
    categoria: str | None = None,
    modalidad: str | None = None,
    comprador: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
) -> dict[str, Any]:
    """Cantidad de licitaciones según los mismos filtros de resumen_licitaciones."""
    params: dict[str, Any] = {
        "mainProcurementCategoryDetails": categoria,
        "procurementMethodDetails": modalidad,
        "buyer": comprador,
        "tenderPeriod_from": desde,
        "tenderPeriod_until": hasta,
    }
    return get_client().minimal_tenders_count(**{k: v for k, v in params.items() if v is not None})


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP server DNCP Paraguay (contrataciones.gov.py)")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
