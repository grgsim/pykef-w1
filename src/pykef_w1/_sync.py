from __future__ import annotations

import asyncio
import functools
import inspect
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .speaker import Speaker


class SyncWrapper:
    """Sync wrapper for async Speaker methods. Cannot be used from async context.

    Each call connects, executes, and disconnects. This avoids orphaned keepalive
    tasks since the event loop only runs during call execution.
    """

    def __init__(self, speaker: Speaker) -> None:
        self._speaker = speaker
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop

    def _run(self, coro: Any) -> Any:
        loop = self._get_loop()
        return loop.run_until_complete(coro)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._speaker, name)
        if not inspect.iscoroutinefunction(attr):
            return attr

        @functools.wraps(attr)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                asyncio.get_running_loop()
                raise RuntimeError("Cannot use sync wrapper from async context")
            except RuntimeError as e:
                if "no running event loop" not in str(e):
                    raise

            try:
                return self._run(attr(*args, **kwargs))
            finally:
                # Disconnect after each call to avoid orphaned keepalive tasks
                self._run(self._speaker.close())

        return sync_wrapper

    def close(self) -> None:
        if self._loop is not None and not self._loop.is_closed():
            self._loop.close()
            self._loop = None
