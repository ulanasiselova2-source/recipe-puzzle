import logging

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.repository import register_user
from keyboards.inline import main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    await register_user(user.id, user.username, user.full_name)
    logger.info("Команда /start, user_id=%s", user.id)
    await message.answer(
        "🍳 <b>Добро пожаловать в «Рецепт-пазл»!</b>\n\n"
        "Угадывай правильные ингредиенты блюда, отмечай лишние и зарабатывай XP.\n"
        "За правильный ответ — 10 XP, за участие — 2 XP.\n\n"
        "Выбирай действие в меню:",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "<b>Команды бота</b>\n"
        "/start — главное меню\n"
        "/game — начать игру\n"
        "/stats — личная статистика\n"
        "/leaderboard — рейтинг игроков\n"
        "/settings — настройки"
    )


@router.callback_query(lambda c: c.data == "menu:home")
async def menu_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🍳 Главное меню. Что будем делать?", reply_markup=main_menu())
    await callback.answer()
