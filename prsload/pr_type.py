from __future__ import annotations

import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PRReview:
    user: str
    requested_at: datetime | None
    first_sign_of_life: datetime | None = None
    first_approve_or_disapprove: datetime | None = None


@dataclass
class PR:
    number: int
    repo_slug: str
    title: str
    url: str
    author: str
    created_at: datetime
    merged_at: datetime | None
    reviews: list[PRReview] = field(default_factory=list)

    @property
    def uid(self):
        return f"{self.repo_slug}/pull/{self.number}"
