import logging

from flask import Flask
from flask import render_template

from prsload import github
from prsload.fetch import get_prs_data
from prsload.templatetags.template_filters import choose_color_for_review_time
from prsload.templatetags.template_filters import choose_color_for_missing_reviews
from prsload.top_reviewer import get_top_reviewers

app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
)


@app.route("/")
def index():
    response = github.post_gql_query(query="{ viewer { login } }")

    return render_template(
        "home.html",
        exc=str(response.exc),
        error=response.error,
        data=response.data,
        query=response.query,
    )


@app.route("/top_reviewers")
def top_reviewers():
    return get_top_reviewers()


@app.template_filter("colorful_percentage_for_review_time")
def colorful_percentage_for_review_time(value: float):
    color = choose_color_for_review_time(value)
    return f"<span class='bg-[{color}] text-white p-1 rounded'>{value}&nbsp;%</span>"


@app.template_filter("colorful_percentage_for_missing_reviews")
def colorful_percentage_for_missing_reviews(value: float):
    color = choose_color_for_missing_reviews(value)
    return f"<span class='bg-[{color}] text-white p-1 rounded'>{value}&nbsp;%</span>"
