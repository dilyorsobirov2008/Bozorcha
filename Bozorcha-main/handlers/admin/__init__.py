from aiogram import Router

from handlers.admin.login import router as login_router
from handlers.admin.menu import router as menu_router
from handlers.admin.categories import router as categories_router
from handlers.admin.products import router as products_router
from handlers.admin.orders import router as orders_router
from handlers.admin.statistics import router as statistics_router
from handlers.admin.settings import router as settings_router
from handlers.admin.broadcast import router as broadcast_router

admin_router = Router(name='admin')
admin_router.include_router(login_router)
admin_router.include_router(menu_router)
admin_router.include_router(categories_router)
admin_router.include_router(products_router)
admin_router.include_router(orders_router)
admin_router.include_router(statistics_router)
admin_router.include_router(settings_router)
admin_router.include_router(broadcast_router)
