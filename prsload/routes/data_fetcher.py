import logging

from flask import Blueprint
from flask import render_template

from prsload import duckdb_client
from prsload import github
from prsload.duckdb_client import PRStats
from prsload.pr_type import PR
from prsload.pr_type import PRReview
from prsload.settings import Settings
from prsload.settings import get_settings

logger = logging.getLogger(__name__)

data_fetcher_bp = Blueprint("data_fetcher", __name__)


@data_fetcher_bp.route("/db_view")
def db_view():
    logger.info("Viewing PR analytics from DuckDB")
    return _render_template_data_fetcher(
        title="DB data",
        subtitle="Shows PR data from persistent DuckDB database. Data survives app restarts. "
        "It's stored in prs_analytics.duckdb.",
    )


class PRCleaner:

    @classmethod
    def is_pr_too_old(cls, pr: PR, settings: Settings) -> bool:
        merge_too_old = bool(pr.merged_at and pr.merged_at < settings.OLDEST_VALID_PR_MERGE_DATE)
        create_too_old = bool( pr.created_at < settings.OLDEST_VALID_PR_CREATE_DATE)
        return merge_too_old and create_too_old

    @classmethod
    def sanitize_pr(cls, pr: PR, settings: Settings) -> PR | None:
        if pr.merged_at and pr.merged_at < settings.OLDEST_VALID_PR_MERGE_DATE:
            return None
        if pr.author in settings.PR_AUTHORS_TO_IGNORE:
            return None

        # we are keeping the PR, but still need to clean its' data
        cls._remove_blocklisted_reviewers(pr, settings)
        cls._remove_self_review(pr)
        cls._remove_vacation_reviews(pr, settings)
        return pr

    @classmethod
    def _remove_vacation_reviews(cls, pr: PR, settings: Settings) -> None:
        pr.reviews = [review for review in pr.reviews if not cls._was_reviewer_on_vacation(review, settings)]

    @staticmethod
    def _was_reviewer_on_vacation(review: PRReview, settings: Settings) -> bool:
        if (review_requested := review.requested_at) and (user_vacation_time := settings.VACATION.get(review.user)):
            vacation_start, vacation_end = user_vacation_time
            if vacation_start <= review_requested <= vacation_end:
                logger.info(f"Vacation time, skipping, {review.user}, {review.requested_at}")
                return True
        return False

    @staticmethod
    def _remove_blocklisted_reviewers(pr: PR, settings: Settings) -> None:
        pr.reviews = [review for review in pr.reviews if review.user not in settings.REVIEWERS_TO_IGNORE]

    @staticmethod
    def _remove_self_review(pr: PR) -> None:
        pr.reviews = [review for review in pr.reviews if review.user != pr.author]


@data_fetcher_bp.route("/sync_from_github")
def sync_from_github():
    """Sync data from GitHub to DuckDB database."""
    settings = get_settings()
    blocklisted_repos: list[str] = []
    synced_prs = 0

    logger.info(f"Starting GitHub sync for all repositories {settings.NUM_OF_DAYS=} {settings.GH_LOGIN=}")

    for repo in github.fetch_all_repos(settings.GH_LOGIN):
        if repo.slug in settings.BLOCKLISTED_REPOS:
            blocklisted_repos.append(repo.slug)
            continue

        if repo.total_prs == 0:
            # logger.info(f"Found repo {repo.slug}, but it has no PRs at all")
            continue

        logger.info(f"****OK**** Syncing PRs from GitHub for repo: {repo.slug} {repo.total_prs=}")

        for raw_pr in github.fetch_prs_with_reviews(repo):
            if PRCleaner.is_pr_too_old(raw_pr, settings):
                # Hm... this is just an idea: probably all next PRs will also be too old, so we can stop
                # fetching for this repo
                break

            pr: PR | None = PRCleaner.sanitize_pr(raw_pr, settings)
            if pr is None:
                continue
            duckdb_client.store_pr(pr)
            synced_prs += 1

    logger.info(f"GitHub sync complete. Synced {synced_prs} PRs to DuckDB")

    return _render_template_data_fetcher(
        title="GitHub Sync Complete",
        subtitle=f"Synced {synced_prs} PRs from GitHub to persistent DuckDB database.",
    )


@data_fetcher_bp.route("/recreate_db")
def recreate_db():
    """Reset all DuckDB tables (drop and recreate)."""
    logger.info("Resetting DuckDB tables")
    duckdb_client.recreate_tables()
    return _render_template_data_fetcher(
        title="Database Reset",
        subtitle="All DuckDB tables have been dropped and recreated. Database is now empty.",
    )


@data_fetcher_bp.route("/delete_all_prs")
def delete_all_prs():
    """Delete all PRs and reviews from the database."""
    logger.info("Deleting all PRs from database")
    prs_count, reviews_count = duckdb_client.delete_all_prs()
    return _render_template_data_fetcher(
        title="All PRs Deleted",
        subtitle=f"Deleted {prs_count} PRs and {reviews_count} reviews from the database.",
    )


def _render_template_data_fetcher(*, title: str, subtitle: str):
    stats: PRStats = duckdb_client.get_pr_stats()
    settings = get_settings()
    return render_template(
        "data_fetcher.html",
        title=title,
        subtitle=subtitle,
        stats=stats,
        settings=settings,
    )
