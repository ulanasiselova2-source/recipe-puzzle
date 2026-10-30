from handlers.start import router as start_router
from handlers.recipes import router as recipes_router
from handlers.game import router as game_router
from handlers.stats import router as stats_router
from handlers.settings import router as settings_router

routers = [
    start_router,
    recipes_router,
    game_router,
    stats_router,
    settings_router,
]