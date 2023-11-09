from typing import Iterator

import redis


def get_redis_pool(host: str, password: str) -> Iterator[redis.Redis]:
    try:
        session = redis.from_url(
            f"redis://{host}:6379?decode_responses=True&encoding=utf-8&health_check_interval=2",
            password=password)
        return session
    finally:
        session.close()
