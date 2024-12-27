from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from marshmallow import Schema, fields, post_load

from prsload.prs_settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PRReview:
    user: str
    requested_at: datetime | None
    first_sign_of_life: datetime | None = None
    first_approve_or_disapprove: datetime | None = None

    def was_reviewer_on_vacation(self) -> bool:
        user_vacation_time = get_settings().VACATION.get(self.user)
        if user_vacation_time and self.requested_at:
            vacation_start, vacation_end = user_vacation_time
            if vacation_start <= self.requested_at <= vacation_end:
                logger.info(
                    f"Vacation time, skipping, {self.user}, {self.requested_at}"
                )
                return True
        return False


@dataclass
class PR:
    number: int
    repo: str
    title: str
    url: str
    author: str
    created_at: datetime
    merged_at: datetime | None
    reviews: list[PRReview] = field(default_factory=list)

    @property
    def uid(self):
        return f"{self.repo}/pull/{self.number}"

    def to_json(self):
        return PRSchema().dump(self)

    def is_pr_merge_too_old(self):
        if not self.merged_at:
            return False
        return self.merged_at < get_settings().OLDEST_VALID_PR_MERGE_DATE

    def is_pr_create_too_old(self):
        return self.created_at < get_settings().OLDEST_VALID_PR_CREATE_DATE

    def remove_vacation_reviews(self):
        self.reviews = [
            review for review in self.reviews if not review.was_reviewer_on_vacation()
        ]

    def remove_irrelevant_reviews(self):
        settings = get_settings()
        irrelevant_reviewers = [*settings.REVIEWERS_TO_IGNORE, self.author]
        new_reviews = []
        for review in self.reviews:
            if review.user in irrelevant_reviewers:
                logger.info(f"Ignoring user {review.user}")
                continue
            new_reviews.append(review)
        self.reviews = new_reviews

    def do_ignore_pr(self) -> bool:
        if self.merged_at and self.is_pr_merge_too_old():
            return True
        if self.author in get_settings().PR_AUTHORS_TO_IGNORE:
            return True
        return False


class PRReviewSchema(Schema):
    user = fields.Str()
    requested_at = fields.DateTime(allow_none=True)
    first_sign_of_life = fields.DateTime(allow_none=True)
    first_approve_or_disapprove = fields.DateTime(allow_none=True)

    @post_load
    def make_obj(self, data, **kwargs) -> PRReview:
        return PRReview(
            user=data["user"],
            requested_at=data["requested_at"],
            first_sign_of_life=data["first_sign_of_life"],
            first_approve_or_disapprove=data["first_approve_or_disapprove"],
        )


class PRSchema(Schema):
    number = fields.Integer()
    repo = fields.Str()
    title = fields.Str()
    url = fields.Str()
    author = fields.Str()
    created_at = fields.DateTime()
    merged_at = fields.DateTime(allow_none=True)
    reviews = fields.List(fields.Nested(PRReviewSchema))

    @post_load
    def make_obj(self, data, **kwargs) -> PR:
        return PR(
            number=int(data["number"]),
            repo=data["repo"],
            title=data["title"],
            url=data["url"],
            author=data["author"],
            created_at=data["created_at"],
            merged_at=data["merged_at"],
            reviews=data["reviews"],
        )
