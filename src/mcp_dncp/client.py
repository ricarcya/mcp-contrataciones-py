"""Cliente HTTP para la API de Datos Abiertos de la DNCP (v3).

Documentación oficial: https://www.contrataciones.gov.py/datos/api/v3/doc/
Spec OpenAPI: https://www.contrataciones.gov.py/datos/api/v3/doc/swagger.json
"""

from __future__ import annotations

from typing import Any

import httpx

from .auth import DncpAuth

BASE_URL = "https://www.contrataciones.gov.py/datos/api/v3/doc"


class DncpError(Exception):
    """Error de la API DNCP o de red, con mensaje legible para el LLM."""


class DncpClient:
    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = 120.0,
        request_token: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)
        self._auth = DncpAuth(request_token, client=self._client)

    def close(self) -> None:
        self._client.close()

    def _headers(self) -> dict[str, str]:
        token = self._auth.get_access_token()
        return {"Authorization": token} if token else {}

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            resp = self._client.get(path, params=params, headers=self._headers())
        except httpx.HTTPError as exc:
            raise DncpError(f"Error de red consultando {path}: {exc}") from exc
        if resp.status_code >= 400:
            raise DncpError(f"HTTP {resp.status_code} en {path}: {resp.text[:300]}")
        try:
            return resp.json()
        except ValueError as exc:
            raise DncpError(f"Respuesta no JSON desde {path}") from exc

    # ------------------------------------------------------------------ #
    # Endpoints de detalle
    # ------------------------------------------------------------------ #
    def get_record(self, ocid: str) -> dict[str, Any]:
        return self.get(f"/ocds/record/{ocid}")

    def get_tender(self, tender_id: str) -> dict[str, Any]:
        return self.get(f"/tender/{tender_id}")

    def get_contract(self, contract_id: str) -> dict[str, Any]:
        return self.get(f"/contracts/{contract_id}")

    def get_award(self, award_id: str) -> dict[str, Any]:
        return self.get(f"/awards/{award_id}")

    def get_complaint(self, complaint_id: str) -> dict[str, Any]:
        return self.get(f"/complaints/{complaint_id}")

    def get_supplier(self, ruc: str) -> dict[str, Any]:
        return self.get(f"/suppliers/{ruc}")

    def get_procuring_entity(self, entity_id: str) -> dict[str, Any]:
        return self.get(f"/procuringEntities/{entity_id}")

    # ------------------------------------------------------------------ #
    # Búsquedas
    # ------------------------------------------------------------------ #
    def search_processes(self, **filters: Any) -> dict[str, Any]:
        return self.get("/search/processes", filters or None)

    def search_suppliers(self, **filters: Any) -> dict[str, Any]:
        return self.get("/search/suppliers", filters or None)

    def search_procuring_entities(self, **filters: Any) -> dict[str, Any]:
        return self.get("/search/procuringEntities", filters or None)

    def search_classification(self, **filters: Any) -> dict[str, Any]:
        return self.get("/search/classification", filters or None)

    def search_procurement_intentions(self, **filters: Any) -> dict[str, Any]:
        return self.get("/search/procurementIntentions", filters or None)

    # ------------------------------------------------------------------ #
    # Catálogo y parámetros
    # ------------------------------------------------------------------ #
    def get_parameters(self, **params: Any) -> dict[str, Any]:
        return self.get("/parameters/parameters", params or None)

    def get_procurement_categories(self) -> dict[str, Any]:
        return self.get("/parameters/procurementCategories")

    def get_procurement_methods(self) -> dict[str, Any]:
        return self.get("/parameters/procurementMethods")

    # ------------------------------------------------------------------ #
    # Visualizaciones (resúmenes)
    # ------------------------------------------------------------------ #
    def minimal_tenders(self, **params: Any) -> dict[str, Any]:
        return self.get("/visualizations/minimal/tenders", params or None)

    def minimal_tenders_count(self, **params: Any) -> dict[str, Any]:
        return self.get("/visualizations/minimal/tenders/count", params or None)
