import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import settings, validate_settings
from database.database import init_db, close_db
from handlers import routers


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    validate_settings()
    await init_db()

    session = (
        AiohttpSession(proxy=settings.proxy_url)
        if settings.proxy_url
        else AiohttpSession()
    )

    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="game", description="Начать игру"),
        BotCommand(command="stats", description="Моя статистика"),
        BotCommand(command="leaderboard", description="Топ-10 игроков"),
        BotCommand(command="settings", description="Настройки"),
    ])
    dp = Dispatcher()
    for router in routers:
        dp.include_router(router)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
