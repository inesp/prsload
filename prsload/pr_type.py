from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema


@dataclass
class PRReview:
    user: str
    requested_at: datetime | None
    first_sign_of_life: datetime | None = None
    first_approve_or_disapprove: datetime | None = None


@dataclass
class PR:
    number: int
    repo: str
    title: str
    url: str
    created_at: datetime
    merged_at: datetime | None
    reviews: list[PRReview] = field(default_factory=list)

    @property
    def uid(self):
        return f"{self.repo}/pull/{self.number}"

    def to_json(self):
        return PRSchema().dump(self)


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
            created_at=data["created_at"],
            merged_at=data["merged_at"],
            reviews=data["reviews"],
        )
