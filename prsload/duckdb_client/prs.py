import logging

from prsload.pr_type import PR

from .client import get_connection

logger = logging.getLogger(__name__)


def _insert_pr(pr: PR) -> int:
    """Insert a single PR into DuckDB and return its ID."""
    with get_connection() as conn:
        try:
            # Insert or update the PR using the UNIQUE constraint
            conn.execute(
                """
                INSERT INTO prs
                (number, repo_slug, title, url, author, created_at, merged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (repo_slug, number) DO UPDATE SET
                    title = EXCLUDED.title,
                    url = EXCLUDED.url,
                    author = EXCLUDED.author,
                    created_at = EXCLUDED.created_at,
                    merged_at = EXCLUDED.merged_at
            """,
                [
                    pr.number,
                    pr.repo_slug,
                    pr.title,
                    pr.url,
                    pr.author,
                    pr.created_at,
                    pr.merged_at,
                ],
            )

            # Get the PR ID
            pr_id = conn.execute(
                "SELECT id FROM prs WHERE repo_slug = ? AND number = ?",
                [pr.repo_slug, pr.number],
            ).fetchone()[0]

            logger.debug(f"Inserted PR {pr.repo_slug}#{pr.number} with ID {pr_id}")
            return pr_id

        except Exception as e:
            logger.error(f"Error inserting PR {pr.repo_slug}#{pr.number}: {e}")
            raise


def _insert_reviews(pr: PR, pr_id: int) -> None:
    """Insert reviews for a PR into DuckDB."""
    if not pr.reviews:
        return

    with get_connection() as conn:
        try:
            # Delete existing reviews for this PR first
            conn.execute("DELETE FROM reviews WHERE pr_id = ?", [pr_id])

            # Insert all reviews for this PR
            for review in pr.reviews:
                conn.execute(
                    """
                    INSERT INTO reviews
                    (pr_id, reviewer, requested_at, first_sign_of_life, first_approve_or_disapprove)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    [
                        pr_id,
                        review.user,
                        review.requested_at,
                        review.first_sign_of_life,
                        review.first_approve_or_disapprove,
                    ],
                )

            logger.debug(f"Inserted {len(pr.reviews)} reviews for PR {pr.repo_slug}#{pr.number}")
        except Exception as e:
            logger.error(f"Error inserting reviews for PR {pr.repo_slug}#{pr.number}: {e}")
            raise


def store_pr(pr: PR):
    """Store a complete PR with reviews in DuckDB."""
    pr_id = _insert_pr(pr)
    _insert_reviews(pr, pr_id)
    logger.debug(f"Stored complete PR {pr.repo_slug}#{pr.number} with {len(pr.reviews)} reviews")
