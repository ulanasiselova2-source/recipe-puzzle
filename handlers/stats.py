from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.repository import get_user, leaderboard, user_achievements
from keyboards.inline import main_menu
from services.game_service import calculate_level

router = Router()


async def show_stats(message: Message, telegram_id: int):
    user = await get_user(telegram_id)
    if user is None:
        await message.answer("Сначала нажми /start.")
        return
    achievements = await user_achievements(telegram_id)
    achievement_text = "\n".join(f"• {a}" for a in achievements) if achievements else "Пока нет достижений"
    await message.answer(
        f"📊 <b>Твоя статистика</b>\n\n"
        f"Игрок: {user.display_name}\n"
        f"⭐ XP: {user.xp}\n"
        f"🎚 Уровень: {calculate_level(user.xp)}\n"
        f"🎮 Раундов: {user.games_played}\n"
        f"🏆 Побед: {user.wins}\n\n"
        f"<b>Достижения</b>\n{achievement_text}",
        reply_markup=main_menu(),
    )


@router.message(Command("stats"))
async def stats_command(message: Message):
    await show_stats(message, message.from_user.id)


@router.callback_query(lambda c: c.data == "stats:me")
async def stats_button(callback: CallbackQuery):
    await callback.answer()
    await show_stats(callback.message, callback.from_user.id)


async def show_leaderboard(message: Message):
    users = await leaderboard(10)
    if not users:
        await message.answer("Пока нет игроков. Нажми /start и сыграй первым!")
        return
    lines = []
    for index, user in enumerate(users, start=1):
        lines.append(
            f"{index}. {user.display_name} — ⭐ {user.xp} XP, 🏆 {user.wins} побед"
        )
    await message.answer("<b>🏆 Топ-10 игроков</b>\n\n" + "\n".join(lines), reply_markup=main_menu())


@router.message(Command("leaderboard"))
async def leaderboard_command(message: Message):
    await show_leaderboard(message)


@router.callback_query(lambda c: c.data == "stats:top")
async def leaderboard_button(callback: CallbackQuery):
    await callback.answer()
    await show_leaderboard(callback.message)
