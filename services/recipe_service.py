
import json
import random
from functools import lru_cache
from collections import deque
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "recipes.json"
_recent_slugs = deque(maxlen=30)

COUNTRY_NAMES = {
    "AR": "🇦🇷 Аргентина",
    "AT": "🇦🇹 Австрия",
    "AU": "🇦🇺 Австралия",
    "BE": "🇧🇪 Бельгия",
    "BR": "🇧🇷 Бразилия",
    "CA": "🇨🇦 Канада",
    "CH": "🇨🇭 Швейцария",
    "CL": "🇨🇱 Чили",
    "CN": "🇨🇳 Китай",
    "CO": "🇨🇴 Колумбия",
    "CU": "🇨🇺 Куба",
    "CZ": "🇨🇿 Чехия",
    "DE": "🇩🇪 Германия",
    "DK": "🇩🇰 Дания",
    "EG": "🇪🇬 Египет",
    "ES": "🇪🇸 Испания",
    "FI": "🇫🇮 Финляндия",
    "FR": "🇫🇷 Франция",
    "GB": "🇬🇧 Великобритания",
    "GE": "🇬🇪 Грузия",
    "GR": "🇬🇷 Греция",
    "HU": "🇭🇺 Венгрия",
    "ID": "🇮🇩 Индонезия",
    "IE": "🇮🇪 Ирландия",
    "IL": "🇮🇱 Израиль",
    "IN": "🇮🇳 Индия",
    "IR": "🇮🇷 Иран",
    "IS": "🇮🇸 Исландия",
    "IT": "🇮🇹 Италия",
    "JP": "🇯🇵 Япония",
    "KE": "🇰🇪 Кения",
    "KR": "🇰🇷 Южная Корея",
    "KZ": "🇰🇿 Казахстан",
    "LB": "🇱🇧 Ливан",
    "LT": "🇱🇹 Литва",
    "MA": "🇲🇦 Марокко",
    "MX": "🇲🇽 Мексика",
    "MY": "🇲🇾 Малайзия",
    "MZ": "🇲🇿 Мозамбик",
    "NG": "🇳🇬 Нигерия",
    "NL": "🇳🇱 Нидерланды",
    "NO": "🇳🇴 Норвегия",
    "NP": "🇳🇵 Непал",
    "NZ": "🇳🇿 Новая Зеландия",
    "PE": "🇵🇪 Перу",
    "PH": "🇵🇭 Филиппины",
    "PK": "🇵🇰 Пакистан",
    "PL": "🇵🇱 Польша",
    "PT": "🇵🇹 Португалия",
    "RO": "🇷🇴 Румыния",
    "RU": "🇷🇺 Россия",
    "SA": "🇸🇦 Саудовская Аравия",
    "SE": "🇸🇪 Швеция",
    "SG": "🇸🇬 Сингапур",
    "TH": "🇹🇭 Таиланд",
    "TR": "🇹🇷 Турция",
    "TW": "🇹🇼 Тайвань",
    "UA": "🇺🇦 Украина",
    "US": "🇺🇸 США",
    "UZ": "🇺🇿 Узбекистан",
    "VE": "🇻🇪 Венесуэла",
    "VN": "🇻🇳 Вьетнам",
    "ZA": "🇿🇦 Южно-Африканская Республика",
}

CATEGORY_NAMES = {
    "main": "🍽 Основные блюда",
    "soup": "🍲 Супы",
    "dessert": "🍰 Десерты",
    "salad": "🥗 Салаты",
    "breakfast": "🍳 Завтраки",
    "appetizer": "🥨 Закуски",
    "snack": "🍿 Перекусы",
    "drink": "🥤 Напитки",
    "side": "🥔 Гарниры",
    "side_dish": "🥔 Гарниры",
    "bakery": "🥐 Выпечка",
    "bread": "🍞 Хлеб и выпечка",
    "sauce": "🥣 Соусы",
}

# Расширенный набор неправильных ингредиентов.
# Три варианта случайно выбираются для каждого вопроса.
DECOY_POOL = [
    # Сладости и десертные продукты
    "Шоколад",
    "Клубничное варенье",
    "Сгущённое молоко",
    "Мёд",
    "Карамель",
    "Маршмеллоу",
    "Печенье",
    "Вафли",
    "Какао-порошок",
    "Сахарная пудра",
    "Кленовый сироп",
    "Арахисовая паста",
    "Фруктовый джем",
    "Кокосовая стружка",

    # Овощи и грибы
    "Маринованные огурцы",
    "Свёкла",
    "Редис",
    "Баклажан",
    "Кабачок",
    "Брюссельская капуста",
    "Цветная капуста",
    "Кукуруза",
    "Тыква",
    "Артишок",
    "Спаржа",
    "Сельдерей",
    "Редька",
    "Маринованный перец",
    "Оливки",
    "Шампиньоны",
    "Вяленые томаты",
    "Морская капуста",

    # Фрукты и ягоды
    "Банан",
    "Клубника",
    "Ананас",
    "Манго",
    "Киви",
    "Груша",
    "Персик",
    "Абрикос",
    "Черника",
    "Виноград",
    "Гранат",
    "Папайя",
    "Кокос",
    "Лимонная цедра",
    "Сушёная клюква",

    # Крупы, хлеб и макаронные изделия
    "Кукурузные хлопья",
    "Овсяные хлопья",
    "Гречка",
    "Пшено",
    "Перловка",
    "Булгур",
    "Кускус",
    "Рисовая лапша",
    "Картофельные чипсы",
    "Сухарики",
    "Лаваш",
    "Ржаной хлеб",
    "Панировочные сухари",
    "Манная крупа",

    # Молочные продукты и яйца
    "Йогурт",
    "Сметана",
    "Творог",
    "Рикотта",
    "Маскарпоне",
    "Сливочное мороженое",
    "Козье молоко",
    "Сливки",
    "Плавленый сыр",
    "Перепелиные яйца",

    # Соусы, приправы и специи
    "Соевый соус",
    "Кетчуп",
    "Горчица",
    "Майонез",
    "Терияки",
    "Барбекю-соус",
    "Аджика",
    "Хрен",
    "Корица",
    "Ваниль",
    "Карри",
    "Куркума",
    "Мускатный орех",
    "Гвоздика",
    "Кардамон",
    "Розмарин",
    "Мята",
    "Укроп",
    "Тархун",
    "Кунжут",
    "Мак",
    "Ванильный сахар",

    # Мясо и птица
    "Копчёная колбаса",
    "Бекон",
    "Сосиски",
    "Куриная печень",
    "Утиная грудка",
    "Баранина",
    "Оленина",
    "Кролик",
    "Ветчина",
    "Куриные сердечки",

    # Рыба и морепродукты
    "Копчёный лосось",
    "Сардины",
    "Анчоусы",
    "Крабовое мясо",
    "Кальмар",
    "Осьминог",
    "Мидии",
    "Креветки",
    "Икра",
    "Сельдь",

    # Орехи, семена и бобовые
    "Грецкие орехи",
    "Миндаль",
    "Фисташки",
    "Фундук",
    "Кешью",
    "Семена чиа",
    "Семена льна",
    "Подсолнечные семечки",
    "Нут",
    "Красная фасоль",
    "Чечевица",
    "Зелёный горошек",

    # Напитки и необычные варианты
    "Кофе",
    "Чёрный чай",
    "Матча",
    "Кола",
    "Апельсиновый сок",
    "Кокосовая вода",
    "Квас",
    "Газированная вода",
    "Яблочный уксус",
    "Бальзамический уксус",
    "Кукурузный сироп",
    "Розовая вода",
]


@lru_cache(maxsize=1)
def _load_data() -> dict:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Не найдена база рецептов: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    recipes = data.get("recipes", [])

    if not isinstance(recipes, list) or not recipes:
        raise ValueError("В файле recipes.json не найден список рецептов.")

    return data


def _load_recipes() -> list[dict]:
    return _load_data().get("recipes", [])


def _get_ru(value, default=""):
    if isinstance(value, dict):
        return value.get("ru") or value.get("en") or default
    if isinstance(value, str):
        return value
    return default


def _ingredient_name(ingredient: dict) -> str:
    name = _get_ru(
        ingredient.get("name"),
        "Неизвестный ингредиент",
    )
    note = _get_ru(ingredient.get("note"), "")

    if note:
        return f"{name} ({note})"

    return name


def _format_quantity(ingredient: dict) -> str:
    quantity = ingredient.get("quantity")
    unit = ingredient.get("unit")

    if unit in ("toTaste", "to_taste"):
        return "по вкусу"

    if quantity is None:
        return "количество не указано"

    units = {
        "g": "г",
        "kg": "кг",
        "ml": "мл",
        "l": "л",
        "pcs": "шт.",
        "pc": "шт.",
        "piece": "шт.",
        "pieces": "шт.",
        "tsp": "ч. л.",
        "tbsp": "ст. л.",
        "cup": "стакан",
        "cups": "стакана",
        "pinch": "щепотка",
    }

    formatted_unit = units.get(unit, unit or "")

    if isinstance(quantity, float) and quantity.is_integer():
        quantity = int(quantity)

    if not formatted_unit:
        return str(quantity)

    return f"{quantity} {formatted_unit}"


def get_all_recipes() -> list[dict]:
    return _load_recipes()


def get_recipe_details(slug: str) -> dict | None:
    for recipe in _load_recipes():
        if recipe.get("slug") == slug:
            return recipe
    return None


def get_available_countries() -> list[dict]:
    """Возвращает только страны с распознанными названиями."""
    country_ids = {
        str(recipe["country"]).strip().upper()
        for recipe in _load_recipes()
        if recipe.get("country")
    }

    countries = [
        {
            "id": country_id,
            "title": COUNTRY_NAMES[country_id],
        }
        for country_id in country_ids
        if country_id in COUNTRY_NAMES
    ]

    return sorted(countries, key=lambda item: item["title"])


def get_available_categories() -> list[dict]:
    """Возвращает категории, присутствующие в базе."""
    category_ids = {
        str(recipe["category"]).strip()
        for recipe in _load_recipes()
        if recipe.get("category")
    }

    return [
        {
            "id": category_id,
            "title": CATEGORY_NAMES.get(
                category_id.lower(),
                f"🍴 {category_id.replace('_', ' ').capitalize()}",
            ),
        }
        for category_id in sorted(category_ids)
    ]


def get_puzzle(country: str | None = None) -> dict:
    recipes = _load_recipes()

    if country and country.lower() != "random":
        country = country.strip().upper()
        recipes = [
            recipe
            for recipe in recipes
            if str(recipe.get("country", "")).strip().upper() == country
        ]

        if not recipes:
            raise RuntimeError(
                f"В базе нет рецептов для выбранной страны: {country}"
            )

    candidates = [
        recipe
        for recipe in recipes
        if len(recipe.get("ingredients", [])) >= 4
        and recipe.get("slug") not in _recent_slugs
    ]

    if not candidates:
        candidates = [
            recipe
            for recipe in recipes
            if len(recipe.get("ingredients", [])) >= 4
        ]

    if not candidates:
        raise RuntimeError(
            "Не найдено рецептов с достаточным количеством ингредиентов."
        )

    recipe = random.choice(candidates)
    recipe_ingredients = recipe.get("ingredients", [])

    unique_ingredients = []
    seen_names = set()

    for ingredient in recipe_ingredients:
        name = _ingredient_name(ingredient)

        if name and name.casefold() not in seen_names:
            seen_names.add(name.casefold())
            unique_ingredients.append(ingredient)

    if len(unique_ingredients) < 4:
        raise RuntimeError(
            "В выбранном рецепте слишком мало разных ингредиентов."
        )

    selected_ingredients = unique_ingredients[:6]

    ingredient_details = [
        {
            "name": _ingredient_name(ingredient),
            "quantity": _format_quantity(ingredient),
        }
        for ingredient in selected_ingredients
    ]

    correct = [item["name"] for item in ingredient_details]

    correct_lower = {item.casefold() for item in correct}
    available_decoys = [
        item
        for item in DECOY_POOL
        if item.casefold() not in correct_lower
    ]

    decoys = random.sample(available_decoys, 3)

    options = correct + decoys
    random.shuffle(options)

    nutrition = recipe.get("nutritionPerServing") or {}
    title = _get_ru(recipe.get("name"), "Неизвестное блюдо")
    summary = _get_ru(recipe.get("summary"), "")
    photo = recipe.get("photo") or {}

    _recent_slugs.append(recipe.get("slug"))

    return {
        "id": recipe.get("slug"),
        "slug": recipe.get("slug"),
        "title": title,
        "summary": summary,
        "country": recipe.get("country"),
        "category": recipe.get("category"),
        "ingredients": options,
        "correct": correct,
        "wrong": decoys,
        "calories": nutrition.get("calories"),
        "source_url": photo.get("url"),
        "image": photo.get("url"),
        "original_title": title,
        "steps": [
            _get_ru(step.get("text"), "")
            for step in recipe.get("steps", [])
        ],
        "ingredient_details": ingredient_details,
        "prep_minutes": recipe.get("prepMinutes", 0),
        "cook_minutes": recipe.get("cookMinutes", 0),
        "servings": recipe.get("baseServings", 2),
        "difficulty": recipe.get("difficulty", "medium"),
    }
