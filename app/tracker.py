from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

from .parser import fetch_today_ads, OlxAd


class Tracker:
    """Runs periodic scraping in a background task per chat/filter."""

    def __init__(self, interval_sec: int = 60):
        self._interval = interval_sec
        self._task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._running = False

    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    async def start(self, url: str, on_new_ads: Callable[[list[OlxAd]], asyncio.Future | None]):
        if self.is_running():
            return
        self._running = True
        loop = asyncio.get_running_loop()

        async def _runner():
            try:
                while self._running:
                    ads = await loop.run_in_executor(self._executor, fetch_today_ads, url)
                    if ads:
                        maybe_future = on_new_ads(ads)
                        if maybe_future is not None:
                            try:
                                await maybe_future
                            except Exception:
                                pass
                    await asyncio.sleep(self._interval)
            finally:
                self._running = False

        self._task = asyncio.create_task(_runner())

    async def stop(self):
        self._running = False
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except Exception:
                pass
            self._task = None


