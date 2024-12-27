from __future__ import annotations

import logging
from datetime import timedelta

from prsload.github.prs import PRS_PER_PAGE, fetch_prs_with_reviews
from prsload.github.repos import Repo, fetch_all_repos
from prsload.pr_type import PR, PRSchema
from prsload.prs_settings import get_settings
from prsload.redis_client import decode_value, redis_client

_CACHE_DURATION = timedelta(minutes=120)


logger = logging.getLogger(__name__)


def fetch_all_prs_data() -> list[PR]:
    all_prs = []
    settings = get_settings()
    for repo in fetch_all_repos(settings.GH_LOGIN):
        if repo.slug in settings.BLOCKLISTED_REPOS:
            continue

        repo_prs = _fetch_prs_for_repo(repo)
        all_prs.extend(repo_prs)
    return all_prs


def _fetch_prs_for_repo(repo: Repo) -> list[PR]:
    repo_prs = PRRedis.get_prs_from_redis(repo.slug)
    if repo_prs is None:
        repo_prs = []
        num_of_too_old_prs = 0
        for pr in fetch_prs_with_reviews(repo):
            if pr.is_pr_create_too_old():
                # The PRs are ordered by CreatedAt,
                # so if the first PR is too old, all the other PRs will be too old
                logger.info(f"Stopping fetching PRs for {repo.slug}.")
                break

            if num_of_too_old_prs >= PRS_PER_PAGE:
                # We saw a whole PAGE full of too old PRs, let's just
                # stop the fetching here!
                logger.info(f"Stopping fetching PRs for {repo.slug}.")
                break

            if pr.is_pr_merge_too_old():
                num_of_too_old_prs += 1
                continue

            repo_prs.append(pr)

        PRRedis.save_prs_to_redis(repo_prs, repo.slug)
    return repo_prs


class PRRedis:
    @staticmethod
    def _build_redis_key(repo_slug: str) -> str:
        num_of_days = get_settings().NUM_OF_DAYS
        return f"prs:{repo_slug}:days_{num_of_days}"

    @classmethod
    def get_prs_from_redis(cls, repo_slug) -> list[PR] | None:
        key = cls._build_redis_key(repo_slug)
        redis_prs_str: str | None = decode_value(redis_client.get(key))  # type: ignore[arg-type]
        if not redis_prs_str:
            return None

        prs = PRSchema(many=True).loads(redis_prs_str)
        logger.info(f"Got data from REDIS for {key=}.")
        return prs

    @classmethod
    def save_prs_to_redis(cls, prs: list[PR], repo_slug: str) -> None:
        serialized_prs = PRSchema(many=True).dumps(prs)
        key = cls._build_redis_key(repo_slug)
        logger.info(f"Will WRITE to redis for {key=}.")

        redis_client.setex(name=key, time=_CACHE_DURATION, value=serialized_prs)
