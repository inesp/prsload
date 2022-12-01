from __future__ import annotations

import logging, dataclasses
import requests, os

logger = logging.getLogger(__name__)

_GQL_URL = "https://api.github.com/graphql"
_TOKEN = os.getenv("GITHUB_API_TOKEN")


@dataclasses.dataclass
class GHResponse:
    query: str
    data: dict | None = None
    exc: Exception | None = None
    error: str | None = None
    response: requests.Response | None = None


def post_gql_query(query: str, variables: dict | None = None) -> GHResponse:
    logger.info(f"Calling Github GraphQL")
    try:
        response: requests.Response = requests.post(
            url=_GQL_URL,
            json={"query": query, "variables": variables or {}},
            headers={
                "Accept": "application/vnd.github.moondragon+json",
                "Authorization": f"Bearer {_TOKEN}",
            },
        )
    except Exception as exc:
        logger.warning(f"Exception occurred: {exc}", exc_info=exc)
        return GHResponse(query=query, exc=exc)

    full_json_data: dict | list | None = _extract_json(response)

    return GHResponse(
        query=query,
        data=_extract_data(full_json_data),
        error=_extract_error(response, full_json_data),
        response=response,
    )


def _extract_json(response: requests.Response) -> dict | None:
    try:
        return response.json()
    except ValueError:
        return None


def _extract_error(response: requests.Response, json_data: dict | None) -> str | None:
    if response.status_code < 200 or response.status_code > 299:
        return f"GH returned status code {response.status_code} instead of 2XX"

    if not json_data:
        return "GH returned no data"

    errors = json_data.get("errors")
    if not errors:
        return None

    user_errors: str = " ".join(errors)
    return f"GH returned errors: {user_errors}"


def _extract_data(json_data: dict | None) -> dict | None:
    if json_data is None:
        return None
    return json_data.get("data")
