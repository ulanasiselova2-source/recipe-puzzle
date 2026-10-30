# Рецепт-пазл

Telegram-бот на Python: игра «найди три лишних ингредиента», XP, уровни, достижения, статистика и рейтинг игроков.

## Технологии
- Python 3.11+
- aiogram 3
- SQLite + SQLAlchemy Async
- YouTube Data API v3 — видео приготовления
- REST Countries API + FlagCDN — данные о стране и флаг
- Локальная база рецептов `data/recipes.json`
- TTL-кэширование, повторные запросы при временных сетевых ошибках

## Установка на Windows
1. Установите Python 3.11 или 3.12.
2. Откройте папку проекта в VS Code.
3. Создайте окружение: `py -3.11 -m venv .venv`
4. Активируйте: `.\.venv\Scripts\Activate.ps1`
5. Установите зависимости: `python -m pip install -r requirements.txt`
6. Скопируйте `.env.example` в `.env` и заполните ключи (`PROXY_URL` — только если нужен прокси).
7. Запустите: `python bot.py`

## Получение ключей
- Telegram: создайте бота через `@BotFather` и скопируйте токен.
- YouTube: в Google Cloud Console создайте проект, включите YouTube Data API v3 и создайте API key.

## База данных
SQLite создаётся автоматически при запуске. Таблицы:
- `users` — профиль, XP, уровень вычисляется из XP, статистика и настройки.
- `game_sessions` — история игровых раундов и результаты.
- `achievements` — полученные достижения.

## Команды
- `/start` — регистрация и меню
- `/game` — начать раунд
- `/stats` — статистика
- `/leaderboard` — топ-10
- `/settings` — уведомления и сброс прогресса
