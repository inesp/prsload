import dataclasses
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from functools import cache
from pathlib import Path
from typing import Any

import yaml

from prsload.constants import DEFAULT_NUM_OF_DAYS
from prsload.exceptions import SettingsError

logger = logging.getLogger(__name__)

_CONFIG_FILE_NAME = "pr-analytics.yml"


@dataclass
class Settings:
    GH_LOGIN: str
    GH_TOKEN: str
    NUM_OF_DAYS: int
    BLOCKLISTED_REPOS: list[str]
    REVIEWERS_TO_IGNORE: list[str]
    PR_AUTHORS_TO_IGNORE: list[str]
    VACATION: dict[str, list[tuple[datetime, datetime]]]

    @property
    def as_dict(self) -> dict[str, str | int | list[str]]:
        return dataclasses.asdict(self)

    @property
    def OLDEST_VALID_PR_MERGE_DATE(self) -> datetime:
        return datetime.now(tz=UTC) - timedelta(days=self.NUM_OF_DAYS)

    @property
    def OLDEST_VALID_PR_CREATE_DATE(self) -> datetime:
        return datetime.now(tz=UTC) - timedelta(days=self.NUM_OF_DAYS + 10)

    @property
    def CONFIG_FILE_NAME(self) -> str:
        return _CONFIG_FILE_NAME


def _load_yaml_config() -> dict[str, Any]:
    config_path = Path(_CONFIG_FILE_NAME)
    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not load {_CONFIG_FILE_NAME}: {e}")
        return {}


def _parse_vacation_data(vacation_config: dict) -> dict[str, list[tuple[datetime, datetime]]]:
    vacation: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    raw_user_vacations: dict | list[dict]
    for user, raw_user_vacations in vacation_config.items():

        user_vacations: list[dict] = (
            [raw_user_vacations] if isinstance(raw_user_vacations, dict) else raw_user_vacations
        )

        for vacation_period in user_vacations:
            start_dt = datetime.fromisoformat(vacation_period["start"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(vacation_period["end"].replace("Z", "+00:00"))
            vacation[user].append((start_dt, end_dt))

    return vacation


@cache
def get_settings() -> Settings:
    gh_token = os.getenv("GH_API_TOKEN")
    gh_login = os.getenv("GH_LOGIN")

    if not gh_token or not gh_login:
        raise SettingsError("GH_API_TOKEN and GH_LOGIN must be set in .env")

    config = _load_yaml_config()

    analysis = config.get("analysis", {})
    users = config.get("users", {})
    repos = config.get("repositories", {})
    vacation_config = config.get("vacation", {})

    num_days: int = int(analysis.get("num_of_days", DEFAULT_NUM_OF_DAYS))
    blocklisted_repos: list[str] = repos.get("blocklisted", [])
    reviewers_ignore: list[str] = users.get("reviewers_to_ignore", [])
    authors_ignore: list[str] = users.get("pr_authors_to_ignore", [])

    return Settings(
        GH_LOGIN=gh_login,
        GH_TOKEN=gh_token,
        NUM_OF_DAYS=num_days,
        BLOCKLISTED_REPOS=blocklisted_repos,
        REVIEWERS_TO_IGNORE=reviewers_ignore,
        PR_AUTHORS_TO_IGNORE=authors_ignore,
        VACATION=_parse_vacation_data(vacation_config),
    )
