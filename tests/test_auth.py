"""Tests de la normalización del request token y del flujo OAuth (mockeado)."""

import base64

import httpx

from mcp_dncp.auth import DncpAuth, _normalize_request_token

KEY = "b5420a1f-4f98-4aef-aa2e-78cec26d6541"
SECRET = "1466bfed-ceda-4f13-9604-7a92a9a28247"
CANONICAL = base64.b64encode(f"{KEY}:{SECRET}".encode()).decode()


def test_normaliza_padding_faltante():
    # token como suele copiarse del portal (sin padding)
    raw = CANONICAL.rstrip("=")
    norm = _normalize_request_token(raw)
    assert norm == CANONICAL
    assert base64.b64decode(norm).decode() == f"{KEY}:{SECRET}"


def test_normaliza_token_ya_canonico():
    assert _normalize_request_token(CANONICAL) == CANONICAL


def test_normaliza_token_no_base64_no_explota():
    # un valor que no es base64 key:secret no debe lanzar; solo se rellena padding
    assert _normalize_request_token("token-raro") == "token-raro=="


def test_get_access_token_envia_request_token_normalizado():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"access_token": "jwt-fake"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    auth = DncpAuth(request_token=CANONICAL.rstrip("="), client=client)
    token = auth.get_access_token()
    assert token == "jwt-fake"
    import json

    assert json.loads(seen["body"])["request_token"] == CANONICAL
    assert auth.enabled is True


def test_sin_token_deshabilitado():
    auth = DncpAuth(request_token=None, client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200))))
    assert auth.enabled is False
    assert auth.get_access_token() is None


def test_token_se_cachea_y_no_repite_post():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"access_token": "jwt-fake"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    auth = DncpAuth(request_token=CANONICAL, client=client)
    assert auth.get_access_token() == "jwt-fake"
    assert auth.get_access_token() == "jwt-fake"  # cacheado, sin nuevo POST
    assert calls["n"] == 1
