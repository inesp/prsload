from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from requests import Response

from prsload.prs_settings import get_settings

logger = logging.getLogger(__name__)

_GQL_URL = "https://api.github.com/graphql"


@dataclass
class GHResponse:
    response: requests.Response
    data: dict


class GitHubException(Exception):
    def __init__(
        self,
        msg: str,
        gql_errors: list[dict] | None = None,
        query: str | None = None,
        variables: dict | None = None,
    ):
        self.gql_errors = gql_errors
        self.query = query
        self.variables = variables
        super().__init__(msg)


def post_gql_query(query: str, variables: dict | None = None) -> GHResponse:
    logger.info(f"Calling Github GraphQL {variables=}")
    token = get_settings().GH_TOKEN
    try:
        response: requests.Response = requests.post(
            url=_GQL_URL,
            json={"query": query, "variables": variables or {}},
            headers={
                "Accept": "application/vnd.github.moondragon+json",
                "Authorization": f"Bearer {token}",
            },
        )
    except Exception as exc:
        logger.warning(f"Exception occurred: {exc}", exc_info=exc)
        raise GitHubException("Request to GitHub raised an exception") from exc

    _check_status_code_of_response(response)
    response_data, json_err = _extract_json_body(response)

    if json_err:
        raise GitHubException(
            "Response is not a valid JSON", query=query, variables=variables
        ) from json_err

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


def _check_status_code_of_response(response: Response) -> None:
    if 200 <= response.status_code <= 299:
        return None

    short_response_text: str = str(response.text)[:200]

    raise GitHubException(
        f"Provider returned code: {response.status_code} "
        f"for {response.request.method} url {response.request.url}. "
        f"Response.text: {short_response_text}"
    )


def _extract_json_body(response: Response) -> tuple[dict | None, ValueError | None]:
    if response.status_code in {201, 204} and len(response.content) == 0:
        # 204 means No data, so there will be nothing to turn into a JSON
        # 201 is often implemented without body
        return {}, None

    try:
        response_data: dict = response.json()
        return response_data, None
    except ValueError as exc:
        return None, exc
