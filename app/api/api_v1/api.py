from fastapi import APIRouter

from app.api.api_v1.endpoints import login, offers, products, users, utils

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(offers.router, prefix="/offers", tags=["offers"])
