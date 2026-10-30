from config import settings
from services.api_client import get_json
from services.cache_service import cache_get, cache_set


async def find_cooking_video(dish_name: str) -> str | None:
    key = "youtube:" + dish_name.lower().strip()
    cached = cache_get(key)
    if cached is not None:
        return cached or None
    if not settings.youtube_api_key:
        raise RuntimeError("Не задан ключ YouTube API")
    data = await get_json(
        "https://www.googleapis.com/youtube/v3/search",
        {
            "key": settings.youtube_api_key,
            "part": "snippet",
            "q": f"{dish_name} recipe cooking",
            "type": "video",
            "maxResults": 1,
            "safeSearch": "strict",
        },
    )
    items = data.get("items", [])
    video_id = items[0].get("id", {}).get("videoId") if items else None
    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
    cache_set(key, url or "")
    return url
