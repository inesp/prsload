from __future__ import annotations

import redis

try:
    # local development
    redis_client = redis.Redis(host="localhost", port=6379)
    redis_client.ping()
except redis.exceptions.ConnectionError:
    # Docker development
    redis_client = redis.Redis(host="redis", port=6379)


def decode_value(raw_val: bytes | None) -> str | None:
    return raw_val.decode("utf-8") if raw_val is not None else None


def ping():
    try:
        return redis_client.ping()
    except redis.exceptions.ConnectionError as exc:
        return str(exc)
