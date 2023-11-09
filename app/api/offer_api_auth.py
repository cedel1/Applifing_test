import httpx
from app.core.config import settings
from fastapi.exceptions import HTTPException
from app.core.redis import get_redis_pool
from redis import Redis
from typing import Iterator


class OAuth2Authorization:
    def __init__(self, client_secret: str, token_url: str, redis_pool: Iterator[Redis]) -> None:
        self.client_secret = client_secret
        self.token_url = token_url
        self.redis_pool = redis_pool

    def __call__(self, ) -> None:
        with self.redis_pool as redis:
            token = redis.get('offer_service_access_token')
            if token is None:
                token = self.refresh_access_token(redis)
        return token

    def refresh_access_token(self, redis: Redis) -> None:
        headers = {'Bearer': self.client_secret, 'accept': 'application/json'}
        try:
            with httpx.Client() as client:
                response = client.post(self.token_url, headers=headers)
                response.raise_for_status()
                token_string = response.json().get("access_token")
                redis.set(
                    'offer_service_access_token',
                    token_string,
                    ex=settings.OFFER_SERVICE_REFRESH_TOKEN_EXPIRE_SECONDS)
                return token_string
        except KeyError as exception:
            raise HTTPException(status_code=400, detail="access token field not received in response")
        except httpx.RequestError as exception:
            raise HTTPException(status_code=400, detail=str(exception))
        except httpx.HTTPStatusError as exception:
            raise HTTPException(status_code=exception.response.status_code, detail=str(exception))


auth_token = OAuth2Authorization(
    client_secret=settings.OFFER_SERVICE_TOKEN,
    token_url=f"{settings.OFFER_SERVICE_BASE_URL}api/v1/auth",
    redis_pool=get_redis_pool(host=settings.REDIS_SERVER, password=settings.REDIS_PASSWORD),
    )
