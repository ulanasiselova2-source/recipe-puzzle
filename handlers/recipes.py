
import math
import random
from html import escape

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from keyboards.inline import (
    recipes_menu_keyboard,
    recipe_categories_keyboard,
    recipe_countries_keyboard,
    recipe_list_keyboard,
    recipe_details_keyboard,
    main_menu,
)
from services.recipe_service import (
    get_all_recipes,
    get_recipe_details,
    get_available_categories,
    get_available_countries,
)


router = Router()

RECIPES_PER_PAGE = 8


class RecipeSearchStates(StatesGroup):
    waiting_for_query = State()


def _recipe_title(recipe: dict) -> str:
    name = recipe.get("name", "Без названия")

    if isinstance(name, dict):
        return str(name.get("ru") or name.get("en") or "Без названия")

    return str(name)


def _recipe_summary(recipe: dict) -> str:
    summary = recipe.get("summary", "")

    if isinstance(summary, dict):
        return str(summary.get("ru") or summary.get("en") or "")

    return str(summary or "")


def _filter_recipes(
    recipes: list[dict],
    category: str | None = None,
    country: str | None = None,
    query: str | None = None,
) -> list[dict]:
    result = recipes

    if category:
        result = [
            recipe
            for recipe in result
            if str(recipe.get("category", "")).lower()
            == category.lower()
        ]

    if country:
        result = [
            recipe
            for recipe in result
            if str(recipe.get("country", "")).upper()
            == country.upper()
        ]

    if query:
        query_lower = query.casefold().strip()
        result = [
            recipe
            for recipe in result
            if query_lower in _recipe_title(recipe).casefold()
            or query_lower in _recipe_summary(recipe).casefold()
            or query_lower in str(recipe.get("slug", "")).casefold()
        ]

    return result


def _recipe_list_text(
    recipes: list[dict],
    page: int,
    total_pages: int,
    heading: str = "🍽 <b>Рецепты</b>",
) -> str:
    if not recipes:
        return (
            f"{heading}\n\n"
            "По этому запросу ничего не найдено. "
            "Попробуй изменить запрос или выбрать другой раздел."
        )

    start = page * RECIPES_PER_PAGE
    visible = recipes[start:start + RECIPES_PER_PAGE]

    lines = [
        heading,
        "",
        f"Найдено рецептов: {len(recipes)}",
        f"Страница {page + 1} из {total_pages}",
        "",
    ]

    for index, recipe in enumerate(visible, start=start + 1):
        lines.append(
            f"{index}. <b>{escape(_recipe_title(recipe))}</b>"
        )

    lines.extend([
        "",
        "Нажми на название блюда, чтобы открыть рецепт.",
    ])

    return "\n".join(lines)


async def _show_recipe_list(
    target: Message | CallbackQuery,
    state: FSMContext,
    recipes: list[dict] | None = None,
    page: int = 0,
    heading: str = "🍽 <b>Рецепты</b>",
    filters: dict | None = None,
):
    if recipes is None:
        recipes = get_all_recipes()

    filters = filters or {}
    total_pages = max(1, math.ceil(len(recipes) / RECIPES_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start = page * RECIPES_PER_PAGE
    visible_recipes = recipes[start:start + RECIPES_PER_PAGE]

    await state.update_data(
        recipe_list=recipes,
        recipe_page=page,
        recipe_heading=heading,
        recipe_filters=filters,
    )

    text = _recipe_list_text(
        recipes,
        page,
        total_pages,
        heading,
    )

    keyboard = recipe_list_keyboard(
        [
            {
                "title": _recipe_title(recipe),
                "slug": recipe.get("slug", ""),
            }
            for recipe in visible_recipes
        ],
        page,
        total_pages,
    )

    if isinstance(target, CallbackQuery):
        if target.message:
            await target.message.edit_text(
                text,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
    else:
        await target.answer(
            text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )


async def _show_recipe_details(
    callback: CallbackQuery,
    slug: str,
):
    recipe = get_recipe_details(slug)

    if not recipe:
        await callback.answer(
            "Рецепт не найден.",
            show_alert=True,
        )
        return

    title = escape(_recipe_title(recipe))
    summary = escape(_recipe_summary(recipe))

    country_id = recipe.get("country")
    category_id = recipe.get("category")

    country_title = "Не указана"
    category_title = "Не указана"

    for country in get_available_countries():
        if country["id"] == str(country_id).upper():
            country_title = country["title"]
            break

    for category in get_available_categories():
        if category["id"] == category_id:
            category_title = category["title"]
            break

    ingredients = recipe.get("ingredients", [])
    ingredient_lines = []

    for ingredient in ingredients:
        if isinstance(ingredient, dict):
            name = ingredient.get("name", "Ингредиент")

            if isinstance(name, dict):
                name = name.get("ru") or name.get("en") or "Ингредиент"

            quantity = ingredient.get("quantity")
            unit = ingredient.get("unit", "")

            if quantity is not None:
                ingredient_lines.append(
                    f"• {escape(str(name))} — "
                    f"{escape(str(quantity))} {escape(str(unit))}"
                )
            else:
                ingredient_lines.append(f"• {escape(str(name))}")
        else:
            ingredient_lines.append(f"• {escape(str(ingredient))}")

    steps = recipe.get("steps", [])
    step_lines = []

    for index, step in enumerate(steps, start=1):
        if isinstance(step, dict):
            step_text = step.get("text", "")
            if isinstance(step_text, dict):
                step_text = step_text.get("ru") or step_text.get("en") or ""
        else:
            step_text = str(step)

        if step_text:
            step_lines.append(f"{index}. {escape(str(step_text))}")

    prep = recipe.get("prepMinutes")
    cook = recipe.get("cookMinutes")
    servings = recipe.get("baseServings")
    nutrition = recipe.get("nutritionPerServing") or {}
    calories = nutrition.get("calories")

    details = [
        f"🍽 <b>{title}</b>",
        "",
    ]

    if summary:
        details.extend([summary, ""])

    details.extend([
        f"🌍 Кухня: {escape(str(country_title))}",
        f"📂 Категория: {escape(str(category_title))}",
    ])

    if servings:
        details.append(f"🍴 Порций: {escape(str(servings))}")

    if prep is not None:
        details.append(f"🔪 Подготовка: {escape(str(prep))} мин.")

    if cook is not None:
        details.append(f"🔥 Приготовление: {escape(str(cook))} мин.")

    if calories is not None:
        details.append(f"🔥 Калорийность на порцию: {escape(str(calories))} ккал")

    if ingredient_lines:
        details.extend([
            "",
            "🥕 <b>Ингредиенты:</b>",
            *ingredient_lines,
        ])

    if step_lines:
        details.extend([
            "",
            "👩‍🍳 <b>Приготовление:</b>",
            *step_lines,
        ])

    photo = recipe.get("photo") or {}
    photo_url = photo.get("url") if isinstance(photo, dict) else None

    if photo_url:
        details.extend([
            "",
            f'📷 <a href="{escape(str(photo_url), quote=True)}">'
            "Фотография блюда</a>",
        ])

    await callback.message.edit_text(
        "\n".join(details),
        reply_markup=recipe_details_keyboard(slug),
        disable_web_page_preview=True,
    )

    await callback.answer()


@router.callback_query(F.data == "recipes:menu")
async def recipes_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    if callback.message:
        await callback.message.edit_text(
            "🍽 <b>Каталог рецептов</b>\n\n"
            "Выбери, как хочешь найти блюдо.",
            reply_markup=recipes_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data == "recipes:categories")
async def show_categories(callback: CallbackQuery, state: FSMContext):
    categories = get_available_categories()

    if callback.message:
        await callback.message.edit_text(
            "🍲 <b>Категории блюд</b>\n\nВыбери категорию:",
            reply_markup=recipe_categories_keyboard(categories),
        )

    await callback.answer()


@router.callback_query(F.data == "recipes:countries")
async def show_countries(callback: CallbackQuery, state: FSMContext):
    countries = get_available_countries()

    if callback.message:
        await callback.message.edit_text(
            "🌍 <b>Кухни мира</b>\n\nВыбери страну:",
            reply_markup=recipe_countries_keyboard(countries),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("recipes:category:"))
async def show_category_recipes(
    callback: CallbackQuery,
    state: FSMContext,
):
    category = callback.data.split(":", 2)[2]
    recipes = _filter_recipes(
        get_all_recipes(),
        category=category,
    )

    category_title = next(
        (
            item["title"]
            for item in get_available_categories()
            if item["id"] == category
        ),
        category,
    )

    await callback.answer()

    await _show_recipe_list(
        callback,
        state,
        recipes,
        heading=f"🍲 <b>{escape(category_title)}</b>",
        filters={"category": category},
    )


@router.callback_query(F.data.startswith("recipes:country:"))
async def show_country_recipes(
    callback: CallbackQuery,
    state: FSMContext,
):
    country = callback.data.split(":", 2)[2]
    recipes = _filter_recipes(
        get_all_recipes(),
        country=country,
    )

    country_title = next(
        (
            item["title"]
            for item in get_available_countries()
            if item["id"] == country
        ),
        country,
    )

    await callback.answer()

    await _show_recipe_list(
        callback,
        state,
        recipes,
        heading=f"🌍 <b>{escape(country_title)}</b>",
        filters={"country": country},
    )


@router.callback_query(F.data == "recipes:search")
async def start_recipe_search(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.set_state(RecipeSearchStates.waiting_for_query)

    if callback.message:
        await callback.message.answer(
            "🔎 <b>Поиск блюда</b>\n\n"
            "Напиши название блюда или часть названия.\n"
            "Например: паста, суп, салат.\n\n"
            "Для отмены отправь /cancel."
        )

    await callback.answer()


@router.message(RecipeSearchStates.waiting_for_query, F.text)
async def process_recipe_search(
    message: Message,
    state: FSMContext,
):
    query = message.text.strip()

    if query.lower() == "/cancel":
        await state.clear()
        await message.answer(
            "Поиск отменён.",
            reply_markup=recipes_menu_keyboard(),
        )
        return

    if not query:
        await message.answer("Введи название блюда.")
        return

    if len(query) > 50:
        await message.answer("Слишком длинный запрос. Максимум 50 символов.")
        return

    recipes = _filter_recipes(
        get_all_recipes(),
        query=query,
    )

    await state.clear()

    await _show_recipe_list(
        message,
        state,
        recipes,
        heading=f"🔎 <b>Результаты поиска: {escape(query)}</b>",
        filters={"query": query},
    )


@router.callback_query(F.data == "recipes:random")
async def random_recipe(
    callback: CallbackQuery,
    state: FSMContext,
):
    recipes = get_all_recipes()

    if not recipes:
        await callback.answer(
            "В базе нет рецептов.",
            show_alert=True,
        )
        return

    recipe = random.choice(recipes)

    await callback.answer()

    await _show_recipe_details(
        callback,
        recipe.get("slug", ""),
    )


@router.callback_query(F.data.startswith("recipes:show:"))
async def show_recipe(
    callback: CallbackQuery,
    state: FSMContext,
):
    slug = callback.data.split("recipes:show:", 1)[1]
    await _show_recipe_details(callback, slug)


@router.callback_query(F.data.startswith("recipes:page:"))
async def change_recipe_page(
    callback: CallbackQuery,
    state: FSMContext,
):
    try:
        page = int(callback.data.split(":", 2)[2])
    except (ValueError, IndexError):
        await callback.answer("Некорректная страница.", show_alert=True)
        return

    data = await state.get_data()
    recipes = data.get("recipe_list", get_all_recipes())
    heading = data.get("recipe_heading", "🍽 <b>Рецепты</b>")
    filters = data.get("recipe_filters", {})

    await callback.answer()

    await _show_recipe_list(
        callback,
        state,
        recipes,
        page=page,
        heading=heading,
        filters=filters,
    )


@router.callback_query(F.data == "recipes:back")
async def back_to_recipe_list(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    recipes = data.get("recipe_list", get_all_recipes())
    page = data.get("recipe_page", 0)
    heading = data.get("recipe_heading", "🍽 <b>Рецепты</b>")
    filters = data.get("recipe_filters", {})

    await callback.answer()

    await _show_recipe_list(
        callback,
        state,
        recipes,
        page=page,
        heading=heading,
        filters=filters,
    )


