import time

import httpx
from app.core.config import settings
from dateutil import relativedelta
from fastapi.exceptions import HTTPException


class OAuth2Authorization:
    def __init__(self, client_secret: str, token_url: str) -> None:
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None
        self.token_expiration = None

    def __call__(self, forced_token_refresh: bool = False) -> None:
        if self.access_token is None or self.token_expired() or forced_token_refresh:
            self.refresh_access_token()
        return self.access_token

    def token_expired(self) -> bool:
        return self.token_expiration is None or self.token_expiration < time.time()

    def refresh_access_token(self) -> None:
        headers = {"Authorization": f"Bearer: {self.client_secret}"}
        try:
            with httpx.Client() as client:
                response = client.post(self.token_url, headers=headers)
                response.raise_for_status()
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.token_expiration = time.time() + relativedelta(minutes=5)
        except KeyError as exception:
            raise HTTPException(status_code=400, detail="access token field not received in response")
        except httpx.RequestError as exception:
            raise HTTPException(status_code=400, detail=str(exception))
        except httpx.HTTPStatusError as exception:
            raise HTTPException(status_code=exception.response.status_code, detail=str(exception))


auth_token = OAuth2Authorization(
    client_secret=settings.OFFER_SERVICE_TOKEN,
    token_url=f"{settings.OFFER_SERVICE_BASE_URL}/api/v1/auth",
    )
