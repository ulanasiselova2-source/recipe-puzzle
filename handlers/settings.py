import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from database.database import SessionLocal
from database.models import User
from database.repository import get_user, reset_progress
from keyboards.inline import settings_keyboard, confirm_reset_keyboard, main_menu

router = Router()
logger = logging.getLogger(__name__)


async def settings_text(message: Message, telegram_id: int):
    user = await get_user(telegram_id)
    if user is None:
        await message.answer("Сначала нажми /start.")
        return
    await message.answer(
        "⚙️ <b>Настройки</b>\nМожно включить или выключить уведомления или сбросить прогресс.",
        reply_markup=settings_keyboard(user.notifications_enabled),
    )


@router.message(Command("settings"))
async def settings_command(message: Message):
    await settings_text(message, message.from_user.id)


@router.callback_query(lambda c: c.data == "settings:open")
async def settings_button(callback: CallbackQuery):
    await callback.answer()
    await settings_text(callback.message, callback.from_user.id)


@router.callback_query(lambda c: c.data == "settings:toggle")
async def toggle_notifications(callback: CallbackQuery):
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        if user is None:
            await callback.answer("Сначала нажми /start.", show_alert=True)
            return
        user.notifications_enabled = not user.notifications_enabled
        enabled = user.notifications_enabled
        await session.commit()
    await callback.message.edit_reply_markup(reply_markup=settings_keyboard(enabled))
    await callback.answer("Настройки сохранены.")


@router.callback_query(lambda c: c.data == "settings:reset")
async def ask_reset(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ <b>Сбросить весь прогресс?</b>\n"
        "XP, уровень, история игр и достижения будут удалены. Это нельзя отменить.",
        reply_markup=confirm_reset_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:reset_yes")
async def confirm_reset(callback: CallbackQuery):
    done = await reset_progress(callback.from_user.id)
    if done:
        logger.info("Прогресс сброшен: user_id=%s", callback.from_user.id)
        await callback.message.edit_text(
            "✅ Прогресс сброшен. Можно начинать заново!", reply_markup=main_menu()
        )
    else:
        await callback.message.edit_text("Сначала нажми /start.")
    await callback.answer()
