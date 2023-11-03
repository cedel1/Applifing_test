from typing import Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.main import app
from app.models.user import User
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from sqlalchemy_utils.functions import create_database, database_exists

from .utils.overrides import override_get_db
from .utils.test_db import TestingSessionLocal, engine

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db() -> Generator:
    if not database_exists(str(settings.SQLALCHEMY_TESTING_DATABASE_URI)):
        create_database(str(settings.SQLALCHEMY_TESTING_DATABASE_URI))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # the standard init_db cannot be used here in fixture because of db transaction conflicts
    # so it is created directly to db
    db_user = User(email=settings.FIRST_SUPERUSER,
                   hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                   full_name=None,
                   is_superuser=True)
    db.add(db_user)
    db.commit()
    db.flush()

    yield db


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
