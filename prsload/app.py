import logging

from flask import Flask

from prsload import github
from prsload.fetch import get_prs_data
from prsload.top_reviewer import get_top_reviewers

app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
)


@app.route("/health")
def health():
    response = github.post_gql_query(query="{ viewer { login } }")
    if response.exc:
        raise response.exc

    return {
        "exc": str(response.exc),
        "error": response.error,
        "data": response.data,
        "query": response.query,
    }


@app.route("/")
def index():
    return "Congratulations, it's a web app!"


@app.route("/top_reviewers")
def top_reviewers():
    return get_top_reviewers()


@app.route("/average_time_to_review")
def average_time_to_review():
    prs = get_prs_data()
    return {}
