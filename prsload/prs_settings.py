import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import cache
from importlib import import_module


@dataclass
class Settings:
    GH_LOGIN: str
    GH_TOKEN: str
    NUM_OF_DAYS: int = 28
    BLOCKLISTED_REPOS: list[str] = field(default_factory=list)
    REVIEWERS_TO_IGNORE: list[str] = field(default_factory=list)
    PR_AUTHORS_TO_IGNORE: list[str] = field(default_factory=list)
    VACATION: dict[str, tuple[datetime, datetime]] = field(default_factory=dict)

    @property
    def as_dict(self) -> dict[str, str | int | list[str]]:
        return dataclasses.asdict(self)

    @property
    def OLDEST_VALID_PR_MERGE_DATE(self) -> datetime:
        return datetime.now(tz=timezone.utc) - timedelta(days=self.NUM_OF_DAYS)

    @property
    def OLDEST_VALID_PR_CREATE_DATE(self) -> datetime:
        return datetime.now(tz=timezone.utc) - timedelta(days=self.NUM_OF_DAYS + 10)


@cache
def get_settings() -> Settings:
    settings_file = import_module("settings")

    return Settings(
        GH_LOGIN=settings_file.GH_LOGIN,
        GH_TOKEN=settings_file.GH_API_TOKEN,
        NUM_OF_DAYS=getattr(settings_file, "NUM_OF_DAYS", 28),
        BLOCKLISTED_REPOS=getattr(settings_file, "BLOCKLISTED_REPOS", []),
        REVIEWERS_TO_IGNORE=getattr(settings_file, "REVIEWERS_TO_IGNORE", []),
        PR_AUTHORS_TO_IGNORE=getattr(settings_file, "PR_AUTHORS_TO_IGNORE", []),
        VACATION=getattr(settings_file, "VACATION", {}),
    )
