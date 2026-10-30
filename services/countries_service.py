"""Второй внешний API: World Bank (данные о стране) + FlagCDN (флаг).

World Bank Countries API бесплатный и не требует ключа.
(REST Countries v3.1 закрыт, новая версия требует регистрацию.)
"""
import logging

from services.api_client import get_json
from services.cache_service import cache_get, cache_set

logger = logging.getLogger(__name__)

COUNTRY_URL = "https://api.worldbank.org/v2/country/{code}"
POPULATION_URL = "https://api.worldbank.org/v2/country/{code}/indicator/SP.POP.TOTL"
FLAG_URL = "https://flagcdn.com/w640/{code}.png"

REGIONS_RU = {
    "Europe & Central Asia": "Европа и Центральная Азия",
    "East Asia & Pacific": "Восточная Азия и Тихоокеанский регион",
    "Latin America & Caribbean": "Латинская Америка и Карибы",
    "Middle East & North Africa": "Ближний Восток и Северная Африка",
    "Middle East, North Africa, Afghanistan & Pakistan": "Ближний Восток, Северная Африка, Афганистан и Пакистан",
    "North America": "Северная Америка",
    "South Asia": "Южная Азия",
    "Sub-Saharan Africa": "Африка к югу от Сахары",
}


def flag_url(code: str) -> str:
    return FLAG_URL.format(code=code.lower())


def _first_item(data) -> dict | None:
    """World Bank отвечает так: [метаданные, [записи]]."""
    if isinstance(data, list) and len(data) >= 2 and data[1]:
        item = data[1][0]
        return item if isinstance(item, dict) else None
    return None


async def _get_population(code: str) -> int | None:
    try:
        data = await get_json(
            POPULATION_URL.format(code=code),
            {"format": "json", "mrnev": 1},
        )
    except Exception:
        logger.warning("World Bank: не удалось получить население для %s", code)
        return None
    item = _first_item(data)
    value = item.get("value") if item else None
    return int(value) if isinstance(value, (int, float)) else None


async def get_country_info(code: str) -> dict | None:
    """Возвращает данные о стране или None, если сервис недоступен."""
    code = code.strip().upper()
    if len(code) != 2 or not code.isalpha():
        return None

    key = f"country:{code}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    try:
        data = await get_json(COUNTRY_URL.format(code=code), {"format": "json"})
    except Exception:
        logger.warning("World Bank недоступен для %s", code)
        return None

    item = _first_item(data)
    if not item:
        logger.warning("World Bank вернул неожиданный ответ для %s: %.200r", code, data)
        return None

    capital = item.get("capitalCity") or None
    region_en = (item.get("region") or {}).get("value", "")
    region = REGIONS_RU.get(region_en.strip(), region_en.strip()) or None
    population = await _get_population(code)

    if not capital and not region and not population:
        return None

    info = {
        "capital": capital or "—",
        "population": population,
        "region": region or "—",
        "flag": flag_url(code),
    }
    cache_set(key, info)
    return info