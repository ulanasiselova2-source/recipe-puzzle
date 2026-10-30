
import logging
import random
from html import escape

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.repository import register_user, save_game
from keyboards.inline import (
    ingredient_keyboard,
    main_menu,
    game_countries_keyboard,
)
from services.recipe_service import (
    get_puzzle,
    get_available_countries,
)
from services.countries_service import get_country_info
from services.youtube_service import find_cooking_video
from services.game_service import is_answer_correct, calculate_level
from states.game_states import GameStates


router = Router()
logger = logging.getLogger(__name__)


def difficulty_ru(value):
    labels = {
        "easy": "Лёгкий",
        "medium": "Средний",
        "hard": "Сложный",
    }
    return labels.get(str(value).lower(), "Не указана")


def country_title(country_id):
    for country in get_available_countries():
        if str(country["id"]).upper() == str(country_id).upper():
            return country["title"]
    return f"🌍 {country_id}"


def game_result_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➡️ Следующий вопрос",
        callback_data="game:next",
    )
    builder.button(
        text="🌍 Поменять страну",
        callback_data="game:change_country",
    )
    builder.button(
        text="🏠 Главное меню",
        callback_data="menu:home",
    )
    builder.adjust(1)
    return builder.as_markup()


async def send_country_card(message: Message, country_id: str):
    """Карточка страны (REST Countries + флаг FlagCDN). Без API — просто пропускаем."""
    info = await get_country_info(country_id)
    if not info:
        return
    population = info.get("population")
    population_text = f"{population:,}".replace(",", " ") if population else "—"
    caption = (
        f"🌍 <b>{escape(country_title(country_id))}</b>\n"
        f"🏛 Столица: {escape(str(info['capital']))}\n"
        f"👥 Население: {population_text}\n"
        f"🧭 Регион: {escape(str(info['region']))}"
    )
    try:
        await message.answer_photo(info["flag"], caption=caption)
    except Exception:
        logger.warning("Не удалось отправить флаг %s", country_id)
        await message.answer(caption)


async def show_country_selection(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(GameStates.choosing_country)

    countries = get_available_countries()

    if not countries:
        await message.answer(
            "В базе пока нет рецептов с указанными странами.",
            reply_markup=main_menu(),
        )
        return

    await message.answer(
        "🌍 <b>Выбери кухню для игры</b>\n\n"
        "Все следующие вопросы будут из выбранной страны.\n"
        "Или нажми «Случайная страна», чтобы бот выбрал за тебя.",
        reply_markup=game_countries_keyboard(countries),
    )


async def start_round(
    message: Message,
    state: FSMContext,
    country: str | None = None,
):
    try:
        puzzle = get_puzzle(country=country)
    except Exception:
        logger.exception("Не удалось получить рецепт из локальной базы")
        await message.answer(
            "Сейчас не удалось загрузить рецепт для выбранной кухни. "
            "Попробуй выбрать другую страну.",
            reply_markup=game_result_keyboard(),
        )
        return

    actual_country = puzzle.get("country") or country

    logger.info("Новый раунд: recipe=%s country=%s", puzzle.get("slug"), actual_country)
    await state.set_state(GameStates.choosing_ingredients)
    await state.update_data(
        puzzle=puzzle,
        selected=[],
        game_country=actual_country,
    )

    ingredients_text = "\n".join(
        f"• {escape(str(ingredient))}"
        for ingredient in puzzle["ingredients"]
    )

    country_text = (
        f"🌍 Кухня: <b>{escape(country_title(actual_country))}</b>\n\n"
        if actual_country
        else ""
    )

    await message.answer(
        f"{country_text}"
        f"🍽 <b>Блюдо: {escape(str(puzzle['title']))}</b>\n\n"
        "В списке есть лишние ингредиенты. "
        "Отметь все три лишние позиции, затем нажми "
        "«Проверить ответ».\n\n"
        f"{ingredients_text}\n\n"
        "💡 Подсказка: лишних ингредиентов ровно три.",
        reply_markup=ingredient_keyboard(puzzle["ingredients"], []),
    )


@router.message(Command("game"))
async def game_command(message: Message, state: FSMContext):
    await show_country_selection(message, state)


@router.callback_query(F.data == "game:start")
async def game_button(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.message:
        await show_country_selection(callback.message, state)


@router.callback_query(F.data == "game:change_country")
async def change_game_country(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    if callback.message:
        await show_country_selection(callback.message, state)


@router.callback_query(F.data.startswith("game:country:"))
async def choose_game_country(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not callback.message:
        await callback.answer()
        return

    country_id = callback.data.rsplit(":", 1)[-1]

    if country_id == "random":
        countries = get_available_countries()

        if not countries:
            await callback.answer(
                "В базе пока нет доступных стран.",
                show_alert=True,
            )
            return

        country_id = random.choice(countries)["id"]

    available_ids = {
        str(item["id"]).upper()
        for item in get_available_countries()
    }

    if str(country_id).upper() not in available_ids:
        await callback.answer(
            "Эта страна не найдена в базе рецептов.",
            show_alert=True,
        )
        return

    await callback.answer(
        f"Выбрана кухня: {country_title(country_id)}"
    )

    await send_country_card(callback.message, country_id)
    await start_round(
        callback.message,
        state,
        country=country_id,
    )


@router.callback_query(F.data == "game:next")
async def next_question(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    country = data.get("game_country")

    await callback.answer()

    if not country:
        if callback.message:
            await show_country_selection(callback.message, state)
        return

    if callback.message:
        await start_round(
            callback.message,
            state,
            country=country,
        )


@router.callback_query(
    GameStates.choosing_ingredients,
    F.data.startswith("pick:"),
)
async def pick_ingredient(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    puzzle = data.get("puzzle")

    if not puzzle:
        await state.clear()
        await callback.answer(
            "Раунд устарел. Начни новую игру.",
            show_alert=True,
        )
        return

    try:
        index = int(callback.data.split(":", 1)[1])
        ingredient = puzzle["ingredients"][index]
    except (ValueError, IndexError, AttributeError):
        await callback.answer(
            "Некорректный выбор.",
            show_alert=True,
        )
        return

    selected = list(data.get("selected", []))

    if ingredient in selected:
        selected.remove(ingredient)
    else:
        if len(selected) >= 3:
            await callback.answer(
                "Можно отметить ровно три ингредиента.",
                show_alert=True,
            )
            return

        selected.append(ingredient)

    await state.update_data(selected=selected)

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=ingredient_keyboard(
                puzzle["ingredients"],
                selected,
            )
        )

    await callback.answer()


@router.callback_query(
    GameStates.choosing_ingredients,
    F.data == "game:check",
)
async def check_answer(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    puzzle = data.get("puzzle")
    selected = data.get("selected", [])

    if not puzzle:
        await state.clear()
        await callback.answer(
            "Раунд устарел. Начни заново.",
            show_alert=True,
        )
        return

    if len(selected) != 3:
        await callback.answer(
            "Сначала отметь ровно три лишних ингредиента.",
            show_alert=True,
        )
        return

    correct = is_answer_correct(selected, puzzle["wrong"])
    user = callback.from_user

    await register_user(
        user.id,
        user.username,
        user.full_name,
    )

    xp, games_played, achievements = await save_game(
        user.id,
        puzzle["title"],
        selected,
        correct,
    )

    level = calculate_level(xp)
    logger.info(
        "Раунд завершён: user_id=%s correct=%s xp=%s", user.id, correct, xp
    )

    try:
        video_url = await find_cooking_video(
            puzzle.get("original_title", puzzle["title"])
        )
    except Exception:
        logger.exception("Не удалось найти видео на YouTube")
        video_url = None

    status = (
        "🎉 <b>Правильно!</b>"
        if correct
        else "❌ <b>Не совсем!</b>"
    )

    wrong_text = ", ".join(
        escape(str(item))
        for item in puzzle.get("wrong", [])
    )

    selected_text = ", ".join(
        escape(str(item))
        for item in selected
    )

    ingredient_details = puzzle.get("ingredient_details", [])

    if ingredient_details:
        actual_ingredients = "\n".join(
            f"• {escape(str(item.get('name', 'Ингредиент')))} — "
            f"{escape(str(item.get('quantity', 'количество не указано')))}"
            for item in ingredient_details
        )
    else:
        actual_ingredients = "\n".join(
            f"• {escape(str(item))}"
            for item in puzzle.get("correct", [])
        )

    calories = puzzle.get("calories")

    if isinstance(calories, (int, float)):
        calories_text = (
            f"{round(calories)} ккал на порцию "
            "(по данным базы рецептов)"
        )
    else:
        calories_text = "не указана в базе рецептов"

    prep = puzzle.get("prep_minutes")
    cook = puzzle.get("cook_minutes")
    difficulty = difficulty_ru(puzzle.get("difficulty"))

    time_parts = []

    if isinstance(prep, (int, float)):
        time_parts.append(f"подготовка — {round(prep)} мин.")

    if isinstance(cook, (int, float)):
        time_parts.append(f"приготовление — {round(cook)} мин.")

    time_text = (
        "\n".join(time_parts)
        if time_parts
        else "Время не указано"
    )

    video_text = (
        f'\n🎥 <a href="{escape(str(video_url), quote=True)}">'
        "Видео приготовления на YouTube</a>"
        if video_url
        else "\n🎥 Видео сейчас найти не удалось."
    )

    source_url = puzzle.get("source_url")

    source_text = (
        f'\n📷 <a href="{escape(str(source_url), quote=True)}">'
        "Фотография рецепта</a>"
        if source_url
        else ""
    )

    achievement_text = (
        "\n" + "\n".join(
            escape(str(item))
            for item in achievements
        )
        if achievements
        else ""
    )

    chosen_country = puzzle.get("country") or data.get("game_country")
    country_text = (
        f"🌍 Кухня: <b>{escape(country_title(chosen_country))}</b>\n"
        if chosen_country
        else ""
    )

    if callback.message:
        await callback.message.edit_text(
            f"{status}\n\n"
            f"{country_text}"
            f"🍽 Блюдо: <b>{escape(str(puzzle['title']))}</b>\n"
            f"❌ Лишние ингредиенты: <b>{wrong_text}</b>\n"
            f"📝 Твой выбор: {selected_text}\n\n"
            f"🥕 <b>Ингредиенты настоящего рецепта:</b>\n"
            f"{actual_ingredients or 'Нет данных'}\n\n"
            f"⏱ <b>Время:</b>\n{time_text}\n"
            f"📊 <b>Сложность:</b> {difficulty}\n"
            f"🔥 <b>Калорийность:</b> {calories_text}\n\n"
            f"⭐ Начислено XP: {10 if correct else 2}\n"
            f"📈 Всего XP: {xp} | Уровень: {level}\n"
            f"🎮 Сыграно раундов: {games_played}"
            f"{video_text}{source_text}{achievement_text}",
            reply_markup=game_result_keyboard(),
            disable_web_page_preview=True,
        )

    await state.set_state(GameStates.showing_result)
    await state.update_data(
        puzzle=None,
        selected=[],
        game_country=chosen_country,
    )
    await callback.answer()

    photo_url = puzzle.get("image")
    if photo_url and callback.message:
        try:
            await callback.message.answer_photo(
                photo_url,
                caption=f"📷 {escape(str(puzzle['title']))}",
            )
        except Exception:
            logger.warning("Не удалось отправить фото блюда")


@router.callback_query(F.data == "game:cancel")
async def cancel_game(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    if callback.message:
        await callback.message.edit_text(
            "Раунд отменён. Возвращаемся в меню.",
            reply_markup=main_menu(),
        )

    await callback.answer()
