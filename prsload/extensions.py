from typing import TYPE_CHECKING

from prsload.templatetags.template_filters import choose_color_for_missing_reviews
from prsload.templatetags.template_filters import choose_color_for_review_time

if TYPE_CHECKING:
    from flask import Flask


def register_template_filters(app: "Flask") -> None:
    """Register custom template filters"""

    @app.template_filter("colorful_percentage_for_review_time")
    def colorful_percentage_for_review_time(value: float) -> str:
        color = choose_color_for_review_time(value)
        return f"<span class='bg-[{color}] text-white p-1 rounded'>{value}&nbsp;%</span>"

    @app.template_filter("colorful_percentage_for_missing_reviews")
    def colorful_percentage_for_missing_reviews(value: float) -> str:
        color = choose_color_for_missing_reviews(value)
        return f"<span class='bg-[{color}] text-white p-1 rounded'>{value}&nbsp;%</span>"
