from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from requests import Response

from prsload.exceptions import GitHubException
from prsload.github.response_utils import check_status_code_of_response
from prsload.github.response_utils import extract_json_body
from prsload.settings import get_settings

logger = logging.getLogger(__name__)

_GQL_URL = "https://api.github.com/graphql"


@dataclass
class GHResponse:
    response: Response
    data: dict


def post_gql_query(query: str, variables: dict | None = None) -> GHResponse:
    logger.info(f"Calling Github GraphQL {variables=}")
    token = get_settings().GH_TOKEN
    try:
        response: Response = requests.post(
            url=_GQL_URL,
            json={"query": query, "variables": variables or {}},
            headers={
                "Accept": "application/vnd.github.moondragon+json",
                "Authorization": f"Bearer {token}",
            },
            timeout=30,
        )
    except Exception as exc:
        logger.warning(f"Exception occurred: {exc}", exc_info=exc)
        raise GitHubException("Request to GitHub raised an exception") from exc

    check_status_code_of_response(response)
    response_data, json_err = extract_json_body(response)

    if json_err:
        raise GitHubException("Response is not a valid JSON", query=query, variables=variables) from json_err

    if response_data is None:
        raise GitHubException("Response was None", query=query, variables=variables)

    gql_data: dict | None = response_data.get("data")
    gql_errors: list[dict] | None = response_data.get("errors")

    if gql_data is None:
        raise GitHubException(
            "Response did not contain any data.",
            gql_errors=gql_errors,
            query=query,
            variables=variables,
        )

    if gql_errors:
        raise GitHubException(
            "Errors in response.",
            gql_errors=gql_errors,
            query=query,
            variables=variables,
        )

    return GHResponse(data=gql_data, response=response)
