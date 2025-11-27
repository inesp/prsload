from requests import Response

from prsload.exceptions import GitHubException


def check_status_code_of_response(response: Response) -> None:
    if 200 <= response.status_code <= 299:
        return

    short_response_text: str = str(response.text)[:200]

    raise GitHubException(
        f"Provider returned code: {response.status_code} "
        f"for {response.request.method} url {response.request.url}. "
        f"Response.text: {short_response_text}"
    )


def extract_json_body(response: Response) -> tuple[dict | None, ValueError | None]:
    if response.status_code in {201, 204} and len(response.content) == 0:
        # 204 means No data, so there will be nothing to turn into a JSON
        # 201 is often implemented without body
        return {}, None

    try:
        response_data: dict = response.json()
        return response_data, None
    except ValueError as exc:
        return None, exc
