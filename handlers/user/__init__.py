from aiogram import Router

from handlers.user.start import router as start_router
from handlers.user.catalog import router as catalog_router
from handlers.user.cart import router as cart_router
from handlers.user.order import router as order_router

user_router = Router(name='user')
user_router.include_router(start_router)
user_router.include_router(catalog_router)
user_router.include_router(cart_router)
user_router.include_router(order_router)
