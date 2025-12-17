from __future__ import annotations

import logging
from collections.abc import Generator
from datetime import datetime

from prsload.date_utils import parse_str_to_date
from prsload.dict_utils import safe_traverse
from prsload.github import client
from prsload.github.client import GHResponse
from prsload.github.gql_utils import extract_gql_query_from_file
from prsload.github.gql_utils import parse_page_info
from prsload.github.repos import Repo
from prsload.pr_type import PR
from prsload.pr_type import PRReview

logger = logging.getLogger(__name__)

THasMorePages = bool
TAfterCursor = str | None

PRS_PER_PAGE = 100


def fetch_prs_with_reviews(repo: Repo) -> Generator[PR]:
    logger.info(f"---------- Fetching PRs from repo `{repo.slug}`")
    query: str = extract_gql_query_from_file("prsload/github/prs.graphql")

    has_more_pages: THasMorePages = True
    after_cursor: TAfterCursor = None

    while has_more_pages:
        one_page_response = client.post_gql_query(
            query=query,
            variables=dict(
                owner=repo.owner,
                name=repo.name,
                limit=PRS_PER_PAGE,
                **dict(afterCursor=after_cursor) if after_cursor else {},
            ),
        )
        yield from _process_one_page_of_prs(one_page_response, repo)
        has_more_pages, after_cursor = _extract_page_info(one_page_response)
    return


def _process_one_page_of_prs(response: GHResponse, repo: Repo) -> Generator[PR]:
    raw_prs: list[dict] = response.data["repository"]["pullRequests"]["nodes"]

    logger.info(f"Processing PRs for {repo.slug}.")

    for pr_data in raw_prs:
        merged_at: str = pr_data["mergedAt"]
        closed_at: str = pr_data["closedAt"]

        pr_author: str = pr_data["author"]["login"]
        pr_number: int = int(pr_data["number"])
        pr = PR(
            number=pr_number,
            repo_slug=repo.slug,
            title=pr_data["title"],
            url=pr_data["url"],
            author=pr_author,
            created_at=parse_str_to_date(pr_data["createdAt"]),
            merged_at=(parse_str_to_date(merged_at or closed_at) if merged_at or closed_at else None),
        )

        logger.info(f"Found PR(number={pr_number}), url={pr.url}, {merged_at=}")

        has_too_many_timeline_items = pr_data["timelineItems"]["pageInfo"]["hasNextPage"]
        if has_too_many_timeline_items > 100:
            logger.warning(
                f"We never implemented a solution for when timelineItems.totalCount > 100. "
                f"{repo.slug} {pr_number=}"
            )

        reviews_by_user: dict[str, PRReview] = {}
        for raw_review_request in pr_data["timelineItems"]["nodes"]:
            user = safe_traverse(raw_review_request, "requestedReviewer.login")
            raw_date = raw_review_request.get("createdAt")
            if not user or not raw_date or user == pr_author:
                continue

            requested_at: datetime = parse_str_to_date(raw_date)
            if user in reviews_by_user:
                user_review = reviews_by_user[user]
                user_review.requested_at = _min_of_two(user_review.requested_at, requested_at)
            else:
                reviews_by_user[user] = PRReview(user=user, requested_at=requested_at)

        has_too_many_reviews = pr_data["reviews"]["pageInfo"]["hasNextPage"]
        if has_too_many_reviews > 100:
            logger.warning(
                f"We never implemented a solution for when the reviews.totalCount > 100. "
                f"{repo.slug} {pr_number=}"
            )

        for raw_review in pr_data["reviews"]["nodes"]:
            user = raw_review["author"]["login"]
            published_at = parse_str_to_date(raw_review["publishedAt"])
            state = raw_review["state"]

            if user == pr_author:
                continue

            if user not in reviews_by_user:
                reviews_by_user[user] = PRReview(user=user, requested_at=None)
            user_review = reviews_by_user[user]

            user_review.first_sign_of_life = _min_of_two(user_review.first_sign_of_life, published_at)

            if state in {"APPROVED", "CHANGES_REQUESTED"}:
                user_review.first_approve_or_disapprove = _min_of_two(
                    user_review.first_approve_or_disapprove, published_at
                )

        pr.reviews = list(reviews_by_user.values())
        yield pr


def _min_of_two(one: datetime | None, second: datetime) -> datetime:
    if one is None:
        return second
    return min(one, second)


def _extract_page_info(
    one_page_response: GHResponse,
) -> tuple[THasMorePages, TAfterCursor]:
    pr_data: dict | None = safe_traverse(one_page_response.data, "repository.pullRequests")
    return parse_page_info(pr_data)
