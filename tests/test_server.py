"""Tests del server MCP (tools registradas y validaciones sin red)."""

import pytest

from mcp_dncp import server


def test_tools_registradas():
    names = {t.name for t in server.mcp._tool_manager.list_tools()}
    for esperada in (
        "buscar_procesos",
        "obtener_record_ocds",
        "buscar_proveedores",
        "obtener_proveedor",
        "buscar_convocantes",
        "obtener_convocante",
        "obtener_licitacion",
        "obtener_contrato",
        "obtener_adjudicacion",
        "buscar_catalogo",
        "obtener_categorias",
        "obtener_modalidades",
        "resumen_licitaciones",
        "contar_licitaciones",
    ):
        assert esperada in names, f"falta tool {esperada}"


def test_buscar_procesos_requiere_filtro():
    with pytest.raises(ValueError, match="filtro"):
        server.buscar_procesos()


def test_buscar_procesos_con_ocid_ok(monkeypatch):
    class FakeClient:
        def search_processes(self, **filters):
            assert filters["ocid"] == "ocds-03ad3f-487119-1"
            return {"records": []}

    monkeypatch.setattr(server, "get_client", lambda: FakeClient())
    assert server.buscar_procesos(ocid="ocds-03ad3f-487119-1") == {"records": []}


def test_normalizar_estado_alias():
    # alias del portal -> valor real de la API
    assert server._normalizar_estado("Publicado") == "En Convocatoria (Abierta)"
    assert server._normalizar_estado("EN PLAZO") == "En Convocatoria (Abierta)"
    assert server._normalizar_estado("en convocatoria (abierta)") == "En Convocatoria (Abierta)"
    # valores reales pasan intactos
    assert server._normalizar_estado("Adjudicada") == "Adjudicada"
    assert server._normalizar_estado("Anulada o Cancelada") == "Anulada o Cancelada"
    # valores desconocidos se envían tal cual
    assert server._normalizar_estado("Estado inventado") == "Estado inventado"
    assert server._normalizar_estado(None) is None


def test_buscar_procesos_mapea_estado_publicado(monkeypatch):
    class FakeClient:
        def search_processes(self, **filters):
            assert filters["tender.statusDetails"] == "En Convocatoria (Abierta)"
            return {"records": []}

    monkeypatch.setattr(server, "get_client", lambda: FakeClient())
    assert server.buscar_procesos(estado="Publicado", titulo="web") == {"records": []}
