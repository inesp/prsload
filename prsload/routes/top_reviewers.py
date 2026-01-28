import logging
from dataclasses import dataclass
from dataclasses import field
from operator import attrgetter
from statistics import median

from flask import Blueprint
from flask import render_template

from prsload.duckdb_client.client import get_connection
from prsload.settings import get_settings
from prsload.templatetags.template_filters import ALL_COLORS

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/top_reviewers")
def top_reviewers():
    settings = get_settings()

    return render_template(
        "top_reviewers.html",
        title=f"PRs stats for the last {settings.NUM_OF_DAYS} days",
        subtitle="",
        settings=settings,
        workload_stats=_get_workload_stats(),
        speed_stats=_get_speed_stats(),
        scale_colors=ALL_COLORS,
    )


@dataclass
class WorkloadForUser:
    user: str
    prs_where_review_was_requested: set[int] = field(default_factory=set)
    prs_where_commented: set[int] = field(default_factory=set)
    prs_where_review_finished: set[int] = field(default_factory=set)
    prs_where_no_review_response: list[str] = field(default_factory=list)

    @property
    def num_of_finished_reviews(self):
        return len(self.prs_where_review_finished)

    @property
    def percentage_of_prs_with_missing_review(self):
        if len(self.prs_where_review_was_requested) == 0:
            return 0
        return int(100 * len(self.prs_where_no_review_response) / len(self.prs_where_review_was_requested))


def _get_workload_stats() -> list[WorkloadForUser]:
    """Build stats about the workload of every dev.
    How many PRs are they assigned too and how many are they responding too."""

    reviewers = []

    with get_connection() as conn:
        result = conn.execute("""
            SELECT
                r.reviewer,
                -- PRs where review was requested (where reviewer is not null and requested_at is not null)
                GROUP_CONCAT(CASE WHEN r.requested_at IS NOT NULL THEN p.id END) as requested_pr_ids,
                -- PRs where they commented (first_sign_of_life is not null)
                GROUP_CONCAT(CASE WHEN r.first_sign_of_life IS NOT NULL THEN p.id END) as commented_pr_ids,
                -- PRs where they finished review (first_approve_or_disapprove is not null)
                GROUP_CONCAT(CASE WHEN r.first_approve_or_disapprove IS NOT NULL THEN p.id END) as finished_pr_ids,
                -- PRs where they were requested but didn't respond (requested_at not null but first_sign_of_life is null)
                GROUP_CONCAT(CASE WHEN r.requested_at IS NOT NULL AND r.first_sign_of_life IS NULL THEN p.repo_slug || '/pull/' || p.number END) as no_response_pr_ids
            FROM reviews r
            JOIN prs p ON r.pr_id = p.id
            WHERE r.reviewer IS NOT NULL
            GROUP BY r.reviewer
            """).fetchall()  # noqa: E501

        for row in result:
            reviewer, requested_ids, commented_ids, finished_ids, no_response_ids = row

            requested_set: set[int] = set(
                int(pr_id) for pr_id in (requested_ids or "").split(",") if pr_id and pr_id != "None"
            )
            commented_set: set[int] = set(
                int(pr_id) for pr_id in (commented_ids or "").split(",") if pr_id and pr_id != "None"
            )
            finished_set: set[int] = set(
                int(pr_id) for pr_id in (finished_ids or "").split(",") if pr_id and pr_id != "None"
            )
            no_response_set: list[str] = sorted(
                set(str(pr_slug) for pr_slug in (no_response_ids or "").split(",") if pr_slug and pr_slug != "None")
            )

            user_data = WorkloadForUser(
                user=reviewer,
                prs_where_review_was_requested=requested_set,
                prs_where_commented=commented_set,
                prs_where_review_finished=finished_set,
                prs_where_no_review_response=no_response_set,
            )
            reviewers.append(user_data)

    reviewers = sorted(reviewers, key=attrgetter("num_of_finished_reviews"), reverse=True)
    return reviewers


@dataclass
class SpeedForUser:
    user: str
    reaction_times_minutes: list[float] = field(default_factory=list)
    prs_with_no_review: list[str] = field(default_factory=list)

    @property
    def num_of_prs_reviewed(self) -> int:
        return len(self.reaction_times_minutes)

    @property
    def median_reaction_time_minutes(self) -> float:
        return median(self.reaction_times_minutes) if self.reaction_times_minutes else 0

    @property
    def avg_reaction_time_str(self) -> str:
        if not self.reaction_times_minutes:
            return "N/A"

        median_minutes = median(self.reaction_times_minutes)
        hours = int(median_minutes // 60)
        minutes = int(median_minutes % 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def get_num_of_reviews_below(self, minutes: int) -> tuple[int, float]:
        if not self.reaction_times_minutes:
            return (0, 0.0)

        num_below = len([t for t in self.reaction_times_minutes if t <= minutes])
        total_prs = len(self.reaction_times_minutes) + len(self.prs_with_no_review)
        percentage = round((num_below * 100) / total_prs, 0) if total_prs > 0 else 0.0

        return (num_below, percentage)


def _get_speed_stats() -> list[SpeedForUser]:
    speed_stats: list[SpeedForUser] = []
    with get_connection() as conn:
        result = conn.execute("""
          SELECT
              r.reviewer,
              -- Reaction times in minutes for PRs where they reviewed
              GROUP_CONCAT(CASE
                  WHEN r.requested_at IS NOT NULL AND r.first_sign_of_life IS NOT NULL
                  THEN CASE
                      WHEN r.first_sign_of_life >= r.requested_at
                      THEN EXTRACT(EPOCH FROM (r.first_sign_of_life - r.requested_at)) / 60.0
                      ELSE 0
                  END
              END) as reaction_times_minutes,
              -- PRs with no review (requested but no response)
              GROUP_CONCAT(CASE
                  WHEN r.requested_at IS NOT NULL AND r.first_sign_of_life IS NULL
                  THEN p.repo_slug || '/pull/' || p.number
              END) as prs_with_no_review
          FROM reviews r
          JOIN prs p ON r.pr_id = p.id
          WHERE r.reviewer IS NOT NULL
          GROUP BY r.reviewer
        """).fetchall()

        for row in result:
            user, reaction_times_str, prs_with_no_review_str = row

            reaction_times: list[float] = []
            if reaction_times_str:
                reaction_times = [float(t) for t in reaction_times_str.split(",") if t and t != "None"]

            prs_with_no_review: list[str] = []
            if prs_with_no_review_str:
                prs_with_no_review = [pr for pr in prs_with_no_review_str.split(",") if pr and pr != "None"]

            speed_data = SpeedForUser(
                user=user,
                reaction_times_minutes=reaction_times,
                prs_with_no_review=prs_with_no_review,
            )
            speed_stats.append(speed_data)

        x: SpeedForUser  # noqa
        speed_stats = sorted(speed_stats, key=lambda x: x.user)
        speed_stats = sorted(speed_stats, key=lambda x: x.median_reaction_time_minutes)

        return speed_stats
