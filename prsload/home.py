from flask import render_template

from prsload import redis_client
from prsload.github import github
from prsload.prs_settings import get_settings


def get_home_response():
    query = "{ viewer { login } }"
    gh_exc = ""
    errors = ""
    response = None

    try:
        response = github.post_gql_query(query)
    except github.GitHubException as exc:
        gh_exc = exc
        errors = exc.gql_errors

    settings = get_settings()

    redis_response = redis_client.ping()

    return render_template(
        "home.html",
        exc=str(gh_exc),
        errors=errors,
        data=response.data if response else None,
        query=query,
        settings=settings,
        redis_response=redis_response,
    )
