"""Autenticación OAuth contra la API DNCP v3.

El acceso sin credenciales funciona en modo testing (15 llamadas/minuto).
Con un request token (creado en https://www.contrataciones.gov.py/datos/adm/login
→ "Mis aplicaciones") se obtiene un access token con validez de 15 minutos,
que este módulo renueva automáticamente antes de que expire.
"""

from __future__ import annotations

import os
import time

import httpx

OAUTH_URL = "https://www.contrataciones.gov.py/datos/api/v3/doc/oauth/token"
ACCESS_TOKEN_TTL = 15 * 60  # segundos; el access token expira a los 15 min


class DncpAuth:
    """Maneja el request_token → access_token con cache y renovación."""

    def __init__(self, request_token: str | None = None, client: httpx.Client | None = None):
        self.request_token = request_token or os.environ.get("DNCP_REQUEST_TOKEN")
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
