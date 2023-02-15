from __future__ import annotations

import logging
from datetime import datetime

from prsload import github
from prsload.constants import BLOCKLISTED_REPOS
from prsload.constants import PR_AUTHORS_TO_IGNORE
from prsload.constants import PRS_FETCH_PAGES_LIMIT
from prsload.constants import PRS_LIMIT
from prsload.constants import REVIEWERS_TO_IGNORE
from prsload.date_utils import parse_str_to_date
from prsload.dict_utils import safe_traverse
from prsload.pr_type import PR
from prsload.pr_type import PRReview
from prsload.redis_prs import get_prs_from_redis
from prsload.redis_prs import save_prs_to_redis


logger = logging.getLogger(__name__)


def get_prs_data():
    prs = get_prs_from_redis()
    if not prs:
        prs = _fetch_all_pr_data()
        save_prs_to_redis(prs)
    return prs


def _fetch_all_pr_data() -> list[PR]:
    repos = _fetch_all_sleuth_repos()

    all_prs = []
    for owner, name in repos:
        if f"{owner}/{name}" not in BLOCKLISTED_REPOS:
            do_continue = True
            page = 0
            after_cursor = None
            while do_continue and (page := page + 1) <= PRS_FETCH_PAGES_LIMIT:
                logger.info(f"Fetching page {page} for {owner}/{name}")
                prs, after_cursor = _fetch_prs_with_reviews(owner, name, after_cursor)
                do_continue = bool(after_cursor)
                all_prs.extend(prs)

    return all_prs


_repositories_query = """
{
  organization(login:"sleuth-io"){
    repositories(first:100){
      nodes{
        name
        owner{
          login
        }
      }
    }
  }
}
"""


def _fetch_all_sleuth_repos() -> list[tuple[str, str]]:
    response = github.post_gql_query(query=_repositories_query)
    repos: list[tuple[str, str]] = []
    for repo_data in response.data["organization"]["repositories"]["nodes"]:
        repos.append(
            (
                repo_data["owner"]["login"],
                repo_data["name"],
            )
        )
    return repos


_reviews_query = """
query GetPRsWithReviews($owner: String!, $name: String!, $limit: Int!, $afterCursor: String) {
  repository(owner: $owner, name: $name) {
    name
    pullRequests(first: $limit, orderBy: {field: CREATED_AT, direction: DESC}, after: $afterCursor) {
      totalCount
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        number
        title
        url
        createdAt
        mergedAt 
        author {
          login
        }
        reviews(first: 100) {
          totalCount
          nodes {
            author {
              login
            }
            publishedAt
            state
          }
        }
        timelineItems(first: 100, itemTypes:[REVIEW_REQUESTED_EVENT]){
          totalCount
          nodes{
            __typename
            ... on ReviewRequestedEvent{
              requestedReviewer{
                  __typename
                  ... on User{
                    login
                  }
                }
              createdAt
            }
          }
        }
      }
    }
  }
}
"""


def _fetch_prs_with_reviews(
    repo_owner, repo_name, after_cursor: str | None
) -> tuple[list[PR], str | None]:
    repo_long_name = f"{repo_owner}/{repo_name}"
    logger.info(f"---------- Fetching PRs from repo {repo_long_name} {after_cursor=}")
    response = github.post_gql_query(
        query=_reviews_query,
        variables=dict(
            owner=repo_owner,
            name=repo_name,
            limit=PRS_LIMIT,
            **dict(afterCursor=after_cursor) if after_cursor else {},
        ),
    )

    num_of_prs = response.data["repository"]["pullRequests"]["totalCount"]
    end_cursor = response.data["repository"]["pullRequests"]["pageInfo"]["endCursor"]
    has_next_page = response.data["repository"]["pullRequests"]["pageInfo"][
        "hasNextPage"
    ]

    logger.info(f"Found {num_of_prs} PRs, the limit is at {PRS_LIMIT}")

    prs: list[PR] = []
    for pr_data in response.data["repository"]["pullRequests"]["nodes"]:
        merged_at = pr_data["mergedAt"]
        pr_author = pr_data["author"]["login"]
        pr = PR(
            number=int(pr_data["number"]),
            repo=repo_long_name,
            title=pr_data["title"],
            url=pr_data["url"],
            author=pr_author,
            created_at=parse_str_to_date(pr_data["createdAt"]),
            merged_at=parse_str_to_date(merged_at) if merged_at else None,
        )

        if pr_author in PR_AUTHORS_TO_IGNORE:
            logger.info(
                f"Ignoring pr of author {pr_author}: PR(number={pr.number}), url={pr.url}"
            )
            continue

        prs.append(pr)
        logger.info(f"Found PR(number={pr.number}), url={pr.url}")

        num_of_requested_reviews = pr_data["timelineItems"]["totalCount"]
        if num_of_requested_reviews > 100:
            raise NotImplementedError(
                f"We never implemented a solution for when the num of review requests is > 100. {num_of_requested_reviews=} {repo_long_name} {pr=}"
            )

        reviews_by_user: dict[str, PRReview] = {}
        for raw_review_request in pr_data["timelineItems"]["nodes"]:
            user = safe_traverse(raw_review_request, "requestedReviewer.login")
            raw_date = raw_review_request.get("createdAt")
            if (
                not user
                or not raw_date
                or user == pr_author
                or user in REVIEWERS_TO_IGNORE
            ):
                continue

            requested_at: datetime = parse_str_to_date(raw_date)
            if user in reviews_by_user:
                user_review = reviews_by_user[user]
                user_review.requested_at = _min_of_two(
                    user_review.requested_at, requested_at
                )
            else:
                reviews_by_user[user] = PRReview(user=user, requested_at=requested_at)

        num_of_reviews = pr_data["reviews"]["totalCount"]
        if num_of_reviews > 100:
            raise NotImplementedError(
                f"We never implemented a solution for when the num of reviews is > 100. {num_of_reviews=}  {repo_long_name} {pr=}"
            )

        for raw_review in pr_data["reviews"]["nodes"]:
            user = raw_review["author"]["login"]
            published_at = parse_str_to_date(raw_review["publishedAt"])
            state = raw_review["state"]

            if user == pr_author or user in REVIEWERS_TO_IGNORE:
                continue

            if not user in reviews_by_user:
                reviews_by_user[user] = PRReview(user=user, requested_at=None)
            user_review = reviews_by_user[user]

            user_review.first_sign_of_life = _min_of_two(
                user_review.first_sign_of_life, published_at
            )

            if state in {"APPROVED", "CHANGES_REQUESTED"}:
                user_review.first_approve_or_disapprove = _min_of_two(
                    user_review.first_approve_or_disapprove, published_at
                )

        pr.reviews = list(reviews_by_user.values())

    next_after_cursor = end_cursor if has_next_page else None
    return prs, next_after_cursor


def _min_of_two(one: datetime | None, second: datetime) -> datetime:
    if one is None:
        return second
    return min(one, second)
