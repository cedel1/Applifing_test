from typing import Any

from app.core.celery_app import celery_app


def test_celery_should_work() -> Any:
    """
    Test Celery worker.
    """
    result = celery_app.send_task("app.worker.test_celery", args=["testing_celery"])
    assert result.get(timeout=5) == "test task return testing_celery"
