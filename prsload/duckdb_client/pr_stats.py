import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

from prsload.duckdb_client.client import get_connection

logger = logging.getLogger(__name__)


@dataclass
class PRStats:
    total_prs: int = 0
    total_repos: int = 0
    repos: list[tuple[str, int]] = field(default_factory=list)
    youngest_data: datetime | None = None
    error_msg: str | None = None


def get_pr_stats() -> PRStats:
    """Get basic PR statistics from DuckDB."""
    with get_connection() as conn:
        try:
            # Total PRs and repos
            result = conn.execute("""
              SELECT COUNT(*) as total_prs, COUNT(DISTINCT repo_slug) as total_repos
              FROM prs
            """).fetchone()

            total_prs, total_repos = result

            # PRs by repo
            repo_stats = conn.execute("""
              SELECT repo_slug, COUNT(*) as pr_count
              FROM prs
              GROUP BY repo_slug
              ORDER BY pr_count DESC, repo_slug ASC
              """).fetchall()

            # Latest sync time (most recent PR created_at)
            latest_sync = conn.execute("""SELECT MAX(created_at) FROM prs""").fetchone()[0]

            return PRStats(
                total_prs=total_prs,
                total_repos=total_repos,
                repos=[(repo, count) for repo, count in repo_stats],
                youngest_data=latest_sync,
            )

        except Exception as e:
            error_msg = f"Error getting PR stats from DuckDB: {e}"
            logger.error(error_msg)
            return PRStats(error_msg=f"Error getting PR stats from DuckDB: {e}")
