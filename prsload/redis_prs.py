from __future__ import annotations

import logging
from datetime import timedelta

from prsload.pr_type import PR
from prsload.pr_type import PRSchema
from prsload.redis_client import decode_value
from prsload.redis_client import redis_client

CACHE_DURATION = timedelta(minutes=30)
CACHE_KEY = "all_pr_data_7"


logger = logging.getLogger(__name__)


def get_prs_from_redis() -> list[PR] | None:
    redis_prs_str: str | None = decode_value(redis_client.get(CACHE_KEY))
    if not redis_prs_str:
        return None

    prs = PRSchema(many=True).loads(redis_prs_str)
    logger.info(f"Got data from REDIS")
    return prs


def save_prs_to_redis(prs: list[PR]):
    serialized_prs = PRSchema(many=True).dumps(prs)
    logger.info(f"Will WRITE to redis.")

    redis_client.setex(name=CACHE_KEY, time=CACHE_DURATION, value=serialized_prs)
