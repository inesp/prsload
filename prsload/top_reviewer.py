from __future__ import annotations

import dataclasses
import statistics
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from operator import attrgetter

from flask import render_template

from prsload.constants import NO_REVIEW_TIME_HIKE
from prsload.constants import PR_AUTHORS_TO_IGNORE
from prsload.constants import NUM_OF_DAYS
from prsload.constants import REVIEWERS_TO_IGNORE
from prsload.fetch import get_prs_data
from prsload.pr_type import PR
from prsload.templatetags.template_filters import ALL_COLORS


@dataclasses.dataclass
class UserDatForReviewLoad:
    user: str
    prs_where_review_was_requested: set[int] = field(default_factory=set)
    prs_where_commented: set[int] = field(default_factory=set)
    prs_where_review_finished: set[int] = field(default_factory=set)
    prs_where_no_review_response: set[int] = field(default_factory=set)

    @property
    def num_of_finished_reviews(self):
        return len(self.prs_where_review_finished)

    @property
    def percentage_of_prs_with_missing_review(self):
        if len(self.prs_where_review_was_requested) == 0:
            return 0
        return int(
            100
            * len(self.prs_where_no_review_response)
            / len(self.prs_where_review_was_requested)
        )

    # @property
    # def score(self) -> int:
    #     return self.prs_where_review_finished + 2 * self.prs_reviewed_extra -


@dataclasses.dataclass
class UserDataForReviewSpeed:
    user: str
    reaction_times: set[timedelta] = field(default_factory=set)
    reaction_times_for_no_reviews: set[timedelta] = field(default_factory=set)
    prs_with_no_review: set[str] = field(default_factory=set)

    @property
    def num_of_prs_reviewed(self):
        return len(self.reaction_times)

    @property
    def num_of_reviews_above_two_hours(self):
        return len([t for t in self.reaction_times if t > timedelta(hours=2)])

    def get_num_of_reviews_below(self, num_of_minutes) -> tuple[int, float]:
        num_of_reviews: int = len(
            [t for t in self.reaction_times if t <= timedelta(minutes=num_of_minutes)]
        )
        num_of_all_prs: int = len(self.reaction_times) + len(self.prs_with_no_review)
        percentage: float = round((num_of_reviews * 100) / num_of_all_prs, 0)
        return num_of_reviews, percentage

    @property
    def avg_reaction_time(self) -> timedelta:
        all_reaction_times = {*self.reaction_times, *self.reaction_times_for_no_reviews}
        times: list[float] = [t.total_seconds() for t in all_reaction_times]

        if not times:
            return timedelta(seconds=0)

        return timedelta(seconds=statistics.median(times))

    @property
    def avg_reaction_time_str(self) -> str:
        total_seconds = self.avg_reaction_time.total_seconds()
        hours = int(total_seconds // 3600)
        reminder = total_seconds - hours * 3600
        minutes = int(reminder // 60)
        seconds = int(reminder - minutes * 60)

        hours_part = f"{hours}h " if hours else ""

        return f"{hours_part}{minutes}m {seconds}s"

    @property
    def sorted_reaction_times(self):
        return sorted(self.reaction_times, key=lambda dt: dt.total_seconds())


def get_top_reviewers():
    prs = get_prs_data()
    oldest_valid_pr = datetime.now(tz=timezone.utc) - timedelta(days=NUM_OF_DAYS)

    return render_template(
        "top_reviewers.html",
        num_of_days=NUM_OF_DAYS,
        reviewers_with_most_prs=_get_reviewers_sorted_by_num_of_prs(
            prs, oldest_valid_pr
        ),
        fastest_reviewers=_get_reviewers_sorted_by_speed(prs, oldest_valid_pr),
        scale_colors=ALL_COLORS,
    )


def _get_reviewers_sorted_by_speed(
    prs: list[PR], oldest_valid_pr: datetime
) -> list[UserDataForReviewSpeed]:
    data_by_user: dict[str, UserDataForReviewSpeed] = {}
    for pr in prs:
        if pr.merged_at and pr.merged_at < oldest_valid_pr:
            continue

        if pr.author in PR_AUTHORS_TO_IGNORE:
            continue

        for review in pr.reviews:
            user: str = review.user

            if user in PR_AUTHORS_TO_IGNORE or user in REVIEWERS_TO_IGNORE:
                print(f"Ignoring user {user}")
                continue

            if user == pr.author:
                continue

            if user not in data_by_user:
                data_by_user[user] = UserDataForReviewSpeed(user=user)
            review_speed = data_by_user[user]

            end: datetime | None = review.first_sign_of_life
            start: datetime | None = review.requested_at
            if start and not end:
                review_speed.prs_with_no_review.add(pr.url)

                now_or_pr_merged: datetime
                if pr.merged_at:
                    now_or_pr_merged = pr.merged_at + NO_REVIEW_TIME_HIKE
                else:
                    now_or_pr_merged = datetime.now(tz=timezone.utc)

                diff = (
                    now_or_pr_merged - start
                    if now_or_pr_merged >= start
                    else timedelta(seconds=0)
                )
                review_speed.reaction_times_for_no_reviews.add(diff)
            elif start and end:
                # if they reviewed before they were assigned, we reward them with reaction_time=0
                diff = end - start if end >= start else timedelta(seconds=0)
                review_speed.reaction_times.add(diff)
            elif not start and end:
                # if they reviewed, but were never assigned, we reward them with reaction_time=0
                review_speed.reaction_times.add(timedelta(seconds=0))

    all_data: list[UserDataForReviewSpeed] = [
        data for data in data_by_user.values() if data.num_of_prs_reviewed > 0
    ]
    sorted_data = sorted(all_data, key=attrgetter("user"))
    sorted_data = sorted(sorted_data, key=lambda d: d.avg_reaction_time.total_seconds())
    sorted_data = sorted(sorted_data, key=attrgetter("prs_with_no_review"))

    return sorted_data


def _get_reviewers_sorted_by_num_of_prs(prs: list[PR], oldest_valid_pr: datetime):
    data_by_users: dict[str, UserDatForReviewLoad] = {}
    for pr in prs:
        if pr.merged_at and pr.merged_at < oldest_valid_pr:
            continue

        print(f"Handling PR {pr.uid}")
        pr_uid: int = pr.uid
        for review in pr.reviews:
            user = review.user

            if user not in data_by_users:
                data_by_users[user] = UserDatForReviewLoad(user=user)
            user_data = data_by_users[user]

            if review.requested_at:
                user_data.prs_where_review_was_requested.add(pr_uid)
            if review.first_sign_of_life:
                user_data.prs_where_commented.add(pr_uid)
            if review.first_approve_or_disapprove:
                user_data.prs_where_review_finished.add(pr_uid)
            if review.requested_at and not review.first_sign_of_life:
                user_data.prs_where_no_review_response.add(pr_uid)

    all_data: list[UserDatForReviewLoad] = list(data_by_users.values())
    sorted_user_data: list[UserDatForReviewLoad] = sorted(
        all_data, key=attrgetter("user")
    )
    sorted_user_data = sorted(
        sorted_user_data, key=attrgetter("num_of_finished_reviews"), reverse=True
    )
    return sorted_user_data
