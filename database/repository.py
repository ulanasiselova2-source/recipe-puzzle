import json
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import SessionLocal
from database.models import User, GameSession, Achievement


async def register_user(telegram_id: int, username: str | None, display_name: str) -> User:
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                display_name=display_name[:200] or "Игрок",
            )
            session.add(user)
        else:
            user.username = username
            user.display_name = display_name[:200] or "Игрок"
        await session.commit()
        await session.refresh(user)
        return user


async def get_user(telegram_id: int) -> User | None:
    async with SessionLocal() as session:
        return await session.scalar(select(User).where(User.telegram_id == telegram_id))


async def save_game(
    telegram_id: int, recipe_title: str, selected: list[str], correct: bool
) -> tuple[int, int, list[str]]:
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            user = User(telegram_id=telegram_id, display_name="Игрок")
            session.add(user)
            await session.flush()
        earned = 10 if correct else 2
        user.xp += earned
        user.games_played += 1
        if correct:
            user.wins += 1
        session.add(GameSession(
            user_id=user.id,
            recipe_title=recipe_title[:300],
            selected_json=json.dumps(selected, ensure_ascii=False),
            correct=correct,
            xp_earned=earned,
        ))
        new_achievements = []
        if user.games_played == 1:
            session.add(Achievement(user_id=user.id, code="first_game", title="Первый раунд"))
            new_achievements.append("🏅 Достижение: Первый раунд")
        if user.wins >= 5:
            existing = await session.scalar(select(Achievement).where(
                Achievement.user_id == user.id,
                Achievement.code == "five_wins",
            ))
            if existing is None:
                session.add(Achievement(user_id=user.id, code="five_wins", title="Пять побед"))
                new_achievements.append("🏆 Достижение: Пять побед")
        await session.commit()
        return user.xp, user.games_played, new_achievements


async def leaderboard(limit: int = 10) -> list[User]:
    async with SessionLocal() as session:
        result = await session.scalars(
            select(User).order_by(desc(User.xp), desc(User.wins)).limit(limit)
        )
        return list(result.all())


async def user_achievements(telegram_id: int) -> list[str]:
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            return []
        result = await session.scalars(
            select(Achievement.title).where(Achievement.user_id == user.id)
        )
        return list(result.all())


async def reset_progress(telegram_id: int) -> bool:
    """Сбрасывает XP, статистику, историю игр и достижения пользователя."""
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            return False
        await session.execute(delete(GameSession).where(GameSession.user_id == user.id))
        await session.execute(delete(Achievement).where(Achievement.user_id == user.id))
        user.xp = 0
        user.games_played = 0
        user.wins = 0
        await session.commit()
        return True
