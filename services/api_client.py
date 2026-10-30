import asyncio
import logging
from typing import Any

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


async def get_json(
    url: str,
    params: dict[str, Any],
    *,
    attempts: int = 3,
    timeout_seconds: int = 12,
) -> Any:
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    last_error = None
    for attempt in range(attempts):
        try:
            connector = None
            if settings.proxy_url:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(settings.proxy_url)
            async with aiohttp.ClientSession(
                timeout=timeout, connector=connector
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 429 or response.status >= 500:
                        raise aiohttp.ClientResponseError(
                            response.request_info, response.history,
                            status=response.status, message="Временная ошибка API"
                        )
                    response.raise_for_status()
                    return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
            last_error = exc
            logger.warning("Внешний API недоступен (попытка %s/%s)", attempt + 1, attempts)
            if attempt < attempts - 1:
                await asyncio.sleep(1.0 * (attempt + 1))
    raise RuntimeError("Внешний API временно недоступен") from last_error
