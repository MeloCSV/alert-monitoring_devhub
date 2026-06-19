import base64
import logging
from typing import List

import httpx

from alert_monitoring.api.driven.atlassian_assets_repository.models.atlassian_assets_config import AtlassianAssetsConfig
from alert_monitoring.api.driven.http_retry import with_retry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0

ATTR_CSW_CODE = "401"
ATTR_PLATFORM = "426"


class AtlassianAssetsHttpClient:

    def fetch_catalog_objects(self, config: AtlassianAssetsConfig) -> List[dict]:
        url = f"{config.base_url.rstrip('/')}/workspace/{config.workspace_id}/v1/object/aql"
        credentials = base64.b64encode(f"{config.email}:{config.token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        body = {"qlQuery": f"objectTypeId = {config.object_type_id}"}

        objects: List[dict] = []
        start_at = 0
        page_num = 0

        with httpx.Client(verify=config.verify_ssl, timeout=DEFAULT_TIMEOUT) as client:
            while True:
                page_num += 1
                if page_num > config.max_pages:
                    logger.warning(
                        "Se alcanzó max_pages=%d en Atlassian Assets; puede haber objetos sin sincronizar.",
                        config.max_pages,
                    )
                    break

                params = {"startAt": start_at, "maxResults": config.page_size}
                try:
                    response = with_retry(
                        lambda: self._post_page(client, url, headers, params, body),
                        label=f"AtlassianAssets startAt={start_at}",
                    )
                except httpx.HTTPError as exc:
                    logger.error("Error al consultar Atlassian Assets (url=%s, startAt=%s): %s", url, start_at, exc)
                    break

                payload = response.json()
                page = payload.get("values", [])
                if not isinstance(page, list) or not page:
                    break

                objects.extend(page)
                start_at += len(page)

                if len(page) < config.page_size:
                    break

        logger.info("Recuperados %d objetos del catálogo Atlassian Assets", len(objects))
        return objects

    @staticmethod
    def _post_page(
        client: httpx.Client,
        url: str,
        headers: dict,
        params: dict,
        body: dict,
    ) -> httpx.Response:
        response = client.post(url, headers=headers, params=params, json=body)
        response.raise_for_status()
        return response

    @staticmethod
    def extract_attribute(attributes: List[dict], attribute_id: str) -> str | None:
        for attr in attributes:
            if str(attr.get("objectTypeAttributeId")) == attribute_id:
                values = attr.get("objectAttributeValues", [])
                if values:
                    return values[0].get("displayValue")
        return None
