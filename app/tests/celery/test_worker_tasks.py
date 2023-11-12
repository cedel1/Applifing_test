import pytest
from app import crud
from app.celery.worker_tasks import (_get_number_of_batches,
                                     do_download_offers_for_product,
                                     do_download_product_offers)
from app.core.celery_app import celery_app
from app.core.config import settings
from app.tests.conftest import get_mocked_celery, get_mocked_client_get
from app.tests.utils.offer import create_random_offer
from app.tests.utils.product import create_random_product
from httpx import Client
from sqlalchemy.orm import Session

batches_test_data = [
    (0, 1),
    (1, 1),
    (settings.API_MAX_RECORDS_LIMIT + 1, 2),
    (settings.API_MAX_RECORDS_LIMIT * 2, 2),
    (settings.API_MAX_RECORDS_LIMIT * 2 + 1, 3),
    (settings.API_MAX_RECORDS_LIMIT * 2 + (settings.API_MAX_RECORDS_LIMIT - 1), 3),
]


@pytest.mark.parametrize("products_count, expected_number_of_batches", batches_test_data)
def test_get_number_of_batches_should_return_correct_number_of_batches(products_count, expected_number_of_batches):
    number_of_batches = _get_number_of_batches(products_count)
    assert number_of_batches == expected_number_of_batches


def test_do_download_offers_for_product_should_raise_exception_if_client_fails(db: Session):
    with pytest.raises(Exception) as e:
        do_download_offers_for_product(db, product_id="1")
        assert str(e.value) == "Task download_offers_for_product(1) failed"


def test_do_download_offers_for_product_should_succeed(db: Session, monkeypatch):
    monkeypatch.setattr(Client, "get", get_mocked_client_get)

    create_random_product(db, id="6ba7b810-9dad-11d1-80b4-00c04fd430c8")

    result = do_download_offers_for_product(db, product_id="6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    assert result == "Created or updated 1 offers, deleted 0 offers."
    saved_offer = crud.offer.get_multi_by_product(db, product_id="6ba7b810-9dad-11d1-80b4-00c04fd430c8")[0]
    assert str(saved_offer.id) == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    assert saved_offer.price == 12345
    assert saved_offer.items_in_stock == 10


def test_do_download_offers_for_product_should_delete_offer_if_not_present_in_result(db: Session, monkeypatch):
    monkeypatch.setattr(Client, "get", get_mocked_client_get)

    create_random_product(db, id="6ba7b810-9dad-11d1-80b4-00c04fd430c9")
    create_random_offer(db, product_id="6ba7b810-9dad-11d1-80b4-00c04fd430c9")  # not in feed, will delete

    result = do_download_offers_for_product(db, product_id="6ba7b810-9dad-11d1-80b4-00c04fd430c9")
    assert result == "Created or updated 1 offers, deleted 1 offers."
    assert not crud.offer.get_multi_by_product(db, product_id="6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def test_do_download_product_offers(db: Session, clear_db_products: None, monkeypatch):
    monkeypatch.setattr(celery_app, "send_task", get_mocked_celery)

    create_random_product(db, id="6ba7b810-9dad-11d1-80b4-00c04fd440c9")
    create_random_product(db, id="6ba7b810-9dad-11d1-80b4-00c04fd440c8")
    create_random_offer(db, product_id="6ba7b810-9dad-11d1-80b4-00c04fd440c8")
    create_random_offer(db, product_id="6ba7b810-9dad-11d1-80b4-00c04fd440c8")

    result = do_download_product_offers(db)
    assert result == "Send tasks to update offers for 2 product(s)."
