import asyncio
from collections.abc import AsyncIterator

import pytest

from pykef_w1 import Speaker


class MockSpeakerServer:
    """Mock KEF speaker TCP server for testing."""

    def __init__(self) -> None:
        self.state: dict[int, int | bytes] = {
            0x25: 0x32,  # Volume 50%, unmuted
            0x30: 0x02,  # WiFi, on, 20min standby, normal orientation
            0x31: 0x84,  # Stopped (132)
            0x27: 0x05,  # EQ mode: desk+phase, standard bass, normal polarity
            0x28: 0x86,  # Desk dB: -6 + 0.5*6 = -3.0 dB
            0x29: 0x86,  # Wall dB: -3.0 dB
            0x2A: 0x84,  # Treble dB: -2 + 0.5*4 = 0.0 dB
            0x2B: 0x80,  # High pass Hz: 50 + 5*0 = 50 Hz
            0x2C: 0x80,  # Sub out Hz: 40 + 5*0 = 40 Hz
            0x2D: 0x8A,  # Sub gain dB: -10 + 1*10 = 0 dB
            0x26: 0x9E,  # Balance: 30 (centered) | 0x80 = 0x9E
            0x3D: 0x64,  # Volume limit: 100%, disabled
            0x41: 0x01,  # Connection mode: wired
            0x20: b"Test Speaker\x00",  # Device name
        }
        self._server: asyncio.Server | None = None

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle incoming client connections."""
        try:
            while True:
                data = await reader.read(100)
                if not data:
                    break

                response = self._process_command(data)
                writer.write(response)
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    def _process_command(self, data: bytes) -> bytes:
        """Process a command and return response."""
        if len(data) < 3:
            return bytes([0x52, 0x00, 0xFF])

        if data[0] == 0x47:  # GET
            cmd = data[1]
            if cmd in self.state:
                value = self.state[cmd]
                if isinstance(value, bytes):
                    # String response
                    return bytes([0x52, cmd, len(value) | 0x80]) + value
                else:
                    # Byte response
                    return bytes([0x52, cmd, 0x81, value])
            return bytes([0x52, cmd, 0x81, 0xFF])

        elif data[0] == 0x53:  # SET
            cmd = data[1]
            if len(data) >= 4:
                self.state[cmd] = data[3]
            return bytes([0x52, 0x11, 0xFF])  # OK

        return bytes([0x52, 0x00, 0xFF])

    async def start(self, host: str = "127.0.0.1", port: int = 0) -> int:
        """Start the mock server and return the assigned port."""
        self._server = await asyncio.start_server(self.handle_client, host, port)
        addr = self._server.sockets[0].getsockname()
        return addr[1]

    async def stop(self) -> None:
        """Stop the mock server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()


@pytest.fixture
async def mock_server() -> AsyncIterator[tuple[str, int]]:
    """Provide a mock speaker server."""
    server = MockSpeakerServer()
    port = await server.start()
    yield ("127.0.0.1", port)
    await server.stop()


@pytest.fixture
async def speaker(mock_server: tuple[str, int]) -> AsyncIterator[Speaker]:
    """Provide a Speaker connected to mock server."""
    host, port = mock_server
    async with Speaker(host, port=port) as s:
        yield s
