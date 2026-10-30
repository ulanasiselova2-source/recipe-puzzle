
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Играть", callback_data="game:start")
    builder.button(text="🍽 Рецепты", callback_data="recipes:menu")
    builder.button(text="📊 Моя статистика", callback_data="stats:me")
    builder.button(text="🏆 Топ-10", callback_data="stats:top")
    builder.adjust(2, 2)
    return builder.as_markup()


def game_countries_keyboard(countries: list[dict]):
    builder = InlineKeyboardBuilder()

    for country in countries:
        builder.button(
            text=country["title"][:60],
            callback_data=f"game:country:{country['id']}",
        )

    builder.button(
        text="🎲 Случайная страна",
        callback_data="game:country:random",
    )
    builder.button(
        text="⬅️ В главное меню",
        callback_data="menu:home",
    )
    builder.adjust(2)
    return builder.as_markup()


def recipes_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔎 Найти блюдо", callback_data="recipes:search")
    builder.button(text="🍲 Категории", callback_data="recipes:categories")
    builder.button(text="🌍 Кухни стран", callback_data="recipes:countries")
    builder.button(text="🎲 Случайный рецепт", callback_data="recipes:random")
    builder.button(text="⬅️ В главное меню", callback_data="menu:home")
    builder.adjust(1)
    return builder.as_markup()


def recipe_categories_keyboard(categories: list[dict]):
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.button(
            text=category["title"][:60],
            callback_data=f"recipes:category:{category['id']}",
        )

    builder.button(text="⬅️ Назад", callback_data="recipes:menu")
    builder.adjust(2)
    return builder.as_markup()


def recipe_countries_keyboard(countries: list[dict]):
    builder = InlineKeyboardBuilder()

    for country in countries:
        builder.button(
            text=country["title"][:60],
            callback_data=f"recipes:country:{country['id']}",
        )

    builder.button(text="⬅️ Назад", callback_data="recipes:menu")
    builder.adjust(2)
    return builder.as_markup()


def recipe_list_keyboard(
    recipes: list[dict],
    page: int = 0,
    total_pages: int = 1,
):
    builder = InlineKeyboardBuilder()

    for recipe in recipes:
        builder.button(
            text=recipe["title"][:60],
            callback_data=f"recipes:show:{recipe['slug']}",
        )

    if page > 0:
        builder.button(
            text="⬅️ Назад",
            callback_data=f"recipes:page:{page - 1}",
        )

    if page + 1 < total_pages:
        builder.button(
            text="➡️ Далее",
            callback_data=f"recipes:page:{page + 1}",
        )

    builder.button(text="🔎 Поиск", callback_data="recipes:search")
    builder.button(text="🍽 К меню рецептов", callback_data="recipes:menu")
    builder.adjust(1)
    return builder.as_markup()


def recipe_details_keyboard(slug: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ К списку рецептов",
        callback_data="recipes:back",
    )
    builder.button(
        text="🍽 К меню рецептов",
        callback_data="recipes:menu",
    )
    builder.adjust(1)
    return builder.as_markup()


def ingredient_keyboard(ingredients: list[str], selected: list[str]):
    builder = InlineKeyboardBuilder()

    for index, ingredient in enumerate(ingredients):
        mark = "✅ " if ingredient in selected else ""
        builder.button(
            text=f"{mark}{ingredient[:45]}",
            callback_data=f"pick:{index}",
        )

    builder.button(text="Проверить ответ", callback_data="game:check")
    builder.button(text="Отмена", callback_data="game:cancel")
    builder.adjust(1)
    return builder.as_markup()


def settings_keyboard(enabled: bool):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=(
            "🔔 Уведомления: включены"
            if enabled
            else "🔕 Уведомления: выключены"
        ),
        callback_data="settings:toggle",
    )
    builder.button(text="🗑 Сбросить прогресс", callback_data="settings:reset")
    builder.button(text="⬅️ В меню", callback_data="menu:home")
    builder.adjust(1)
    return builder.as_markup()


def confirm_reset_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, сбросить", callback_data="settings:reset_yes")
    builder.button(text="↩️ Отмена", callback_data="settings:open")
    builder.adjust(2)
    return builder.as_markup()
