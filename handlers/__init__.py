"""
Handler registration module.
Registers all bot handlers (routers) with the dispatcher.
"""


def register_all_handlers(dp):
    """Register all routers with the dispatcher in proper order."""
    from handlers.start import router as start_router
    from handlers.user.catalog import router as catalog_router
    from handlers.user.cart import router as cart_router
    from handlers.user.order import router as order_router
    from handlers.admin.auth import router as admin_auth_router
    from handlers.admin.categories import router as admin_cat_router
    from handlers.admin.products import router as admin_prod_router
    from handlers.admin.orders import router as admin_orders_router
    from handlers.admin.stats import router as admin_stats_router
    from handlers.admin.settings import router as admin_settings_router
    from handlers.admin.broadcast import router as admin_broadcast_router

    dp.include_routers(
        start_router,
        catalog_router,
        cart_router,
        order_router,
        admin_auth_router,
        admin_cat_router,
        admin_prod_router,
        admin_orders_router,
        admin_stats_router,
        admin_settings_router,
        admin_broadcast_router,
    )
