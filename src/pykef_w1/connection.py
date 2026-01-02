import asyncio
import contextlib
from dataclasses import dataclass
from typing import Self

from .exceptions import ConnectionError
from .protocol import GET, Request, Response


@dataclass
class ConnectionConfig:
    host: str
    port: int = 50001
    timeout: float = 2.0
    keepalive: float = 1.0
    max_retries: int = 3
    retry_delay: float = 0.5


class Connection:
    """TCP connection to KEF speaker with auto-disconnect and retry."""

    def __init__(self, config: ConnectionConfig) -> None:
        self._config = config
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._keepalive_task: asyncio.Task[None] | None = None

    @property
    def is_connected(self) -> bool:
        return self._writer is not None

    async def connect(self) -> None:
        async with self._lock:
            if self.is_connected:
                self._reset_keepalive()
                return

            last_err = None
            for attempt in range(self._config.max_retries):
                try:
                    self._reader, self._writer = await asyncio.wait_for(
                        asyncio.open_connection(self._config.host, self._config.port),
                        timeout=self._config.timeout,
                    )
                    self._reset_keepalive()
                    return
                except (TimeoutError, OSError) as e:
                    last_err = e
                    if attempt < self._config.max_retries - 1:
                        await asyncio.sleep(self._config.retry_delay * (2**attempt))

            raise ConnectionError(
                f"Failed to connect to {self._config.host}:{self._config.port}"
            ) from last_err

    async def disconnect(self) -> None:
        self._cancel_keepalive()
        async with self._lock:
            await self._close_writer()

    async def send(self, request: Request) -> Response:
        await self.connect()
        async with self._lock:
            if not self._writer or not self._reader:
                raise ConnectionError("Not connected")

            self._writer.write(request.data)
            await self._writer.drain()

            try:
                data = await asyncio.wait_for(
                    self._reader.read(1024),
                    timeout=self._config.timeout,
                )
            except TimeoutError:
                # from None: suppress chaining, the message already captures the context
                raise ConnectionError("Response timeout") from None

            if not data:
                raise ConnectionError("Connection closed by speaker")

            self._reset_keepalive()
            expected_cmd = request.data[1] if request.data[0] == GET else None
            return Response.parse(data, expected_cmd)

    async def _close_writer(self) -> None:
        if self._writer:
            self._writer.close()
            with contextlib.suppress(Exception):
                await self._writer.wait_closed()
        self._reader = None
        self._writer = None

    def _reset_keepalive(self) -> None:
        self._cancel_keepalive()
        self._keepalive_task = asyncio.create_task(self._keepalive_timeout())

    async def _keepalive_timeout(self) -> None:
        # Don't call disconnect() here - it would cancel ourselves before closing
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.sleep(self._config.keepalive)
            async with self._lock:
                await self._close_writer()
        self._keepalive_task = None

    def _cancel_keepalive(self) -> None:
        if self._keepalive_task:
            self._keepalive_task.cancel()
            self._keepalive_task = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.disconnect()
