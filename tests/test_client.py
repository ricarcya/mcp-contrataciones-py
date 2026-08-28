"""Tests del cliente HTTP con transporte mockeado (sin red)."""

import httpx
import pytest

from mcp_dncp.client import DncpClient, DncpError


def make_client(handler) -> DncpClient:
    return DncpClient(transport=httpx.MockTransport(handler))


def test_search_processes_envia_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"records": [], "pagination": {"total_items": 0}})

    client = make_client(handler)
    result = client.search_processes(ocid="ocds-03ad3f-487119-1", items_per_page=5)
    assert result["pagination"]["total_items"] == 0
    assert seen["path"].endswith("/search/processes")
    assert seen["params"]["ocid"] == "ocds-03ad3f-487119-1"
    assert seen["params"]["items_per_page"] == "5"


def test_get_record_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/ocds/record/ocds-03ad3f-487119-1")
        return httpx.Response(200, json={"records": []})

    result = make_client(handler).get_record("ocds-03ad3f-487119-1")
    assert "records" in result


def test_error_http_es_dncp_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"status": "fail", "message": "Al menos un filtro es requerido"})

    with pytest.raises(DncpError) as exc:
        make_client(handler).search_processes()
    assert "400" in str(exc.value)


def test_sin_credenciales_no_envia_authorization():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"list": []})

    make_client(handler).get_parameters()
