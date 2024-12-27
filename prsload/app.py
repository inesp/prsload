import logging

from flask import Flask

from prsload.home import get_home_response
from prsload.templatetags.template_filters import (
    choose_color_for_missing_reviews,
    choose_color_for_review_time,
)
from prsload.top_reviewer import get_top_reviewers

app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
)


@app.route("/")
def index():
    return get_home_response()


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
