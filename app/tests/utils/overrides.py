from .test_db import TestingSessionLocal


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_auth_token():
    return "3fa85f64-5717-4562-b3fc-2c963f66afa6"
