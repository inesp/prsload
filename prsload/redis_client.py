from __future__ import annotations

import redis

redis_client = redis.Redis(host="redis", port=6379)


def decode_value(raw_val: bytes | None) -> str | None:
    return raw_val.decode("utf-8") if raw_val is not None else None
