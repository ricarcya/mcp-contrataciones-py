"""Autenticación OAuth contra la API DNCP v3.

El acceso sin credenciales funciona en modo testing (15 llamadas/minuto).
Con un request token (creado en https://www.contrataciones.gov.py/datos/adm/login
→ "Mis aplicaciones") se obtiene un access token con validez de 15 minutos,
que este módulo renueva automáticamente antes de que expire.
"""

from __future__ import annotations

import base64
import os
import time

import httpx

OAUTH_URL = "https://www.contrataciones.gov.py/datos/api/v3/doc/oauth/token"
ACCESS_TOKEN_TTL = 15 * 60  # segundos; el access token expira a los 15 min


def _normalize_request_token(token: str) -> str:
    """El portal muestra el request token como base64('<consumer_key>:<consumer_secret>').

    Al copiarlo suele perderse el padding final ('=='), lo que hace que el servidor
    responda 401 'request_token does not match'. Esta función recompone la forma
    canónica: rellena el padding y, si decodifica a <uuid>:<uuid>, re-emite el base64
    exacto que espera la API.
    """
    t = token.strip()
    if len(t) % 4:
        t += "=" * (4 - len(t) % 4)
    try:
        decoded = base64.b64decode(t, validate=True)
        text = decoded.decode("ascii")
        key, _, secret = text.partition(":")
        if len(key) == 36 and len(secret) == 36:
            return base64.b64encode(f"{key}:{secret}".encode()).decode()
    except (ValueError, UnicodeDecodeError):
        pass
    return t


class DncpAuth:
    """Maneja el request_token → access_token con cache y renovación."""

    def __init__(self, request_token: str | None = None, client: httpx.Client | None = None):
        raw = request_token or os.environ.get("DNCP_REQUEST_TOKEN") or ""
        self.request_token = _normalize_request_token(raw)
        self._client = client or httpx.Client(timeout=30.0)
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    @property
    def enabled(self) -> bool:
        return bool(self.request_token)

    def _fetch_token(self) -> str:
        resp = self._client.post(OAUTH_URL, json={"request_token": self.request_token})
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token") or data.get("token") or data.get("accessToken")
        if not token:
            raise RuntimeError(f"oauth/token no devolvió access_token: {data}")
        return str(token)

    def get_access_token(self) -> str | None:
        """Access token vigente, o None si no hay credenciales configuradas."""
        if not self.enabled:
            return None
        if not self._access_token or time.time() > self._expires_at - 60:
            self._access_token = self._fetch_token()
            self._expires_at = time.time() + ACCESS_TOKEN_TTL
        return self._access_token
