from dataclasses import dataclass
from enum import IntEnum
from typing import Self

from .exceptions import ProtocolError

# Protocol prefixes (ASCII: G=GET, S=SET, R=RESPONSE)
GET = 0x47
SET = 0x53
RESPONSE = 0x52
FLAG = 0x80  # High bit flag for length/value fields

OK_RESPONSE = bytes([RESPONSE, 0x11, 0xFF])


class Command(IntEnum):
    """Protocol command bytes. LSX-specific commands are marked."""

    FIRMWARE = 0x11
    HARDWARE = 0x14
    SERIAL_MASTER = 0x15
    SERIAL_SLAVE = 0x16
    DEVICE_NAME = 0x20
    VOLUME = 0x25
    BALANCE = 0x26
    EQ_MODE = 0x27
    DESK_DB = 0x28
    WALL_DB = 0x29
    TREBLE_DB = 0x2A
    HIGH_PASS_HZ = 0x2B
    SUB_OUT_HZ = 0x2C
    SUB_GAIN_DB = 0x2D
    WIFI_SIGNAL = 0x2F
    SOURCE = 0x30
    PLAYBACK = 0x31
    VOLUME_LIMIT = 0x3D
    CABLE_MODE = 0x41  # LSX only
    LSX_UI = 0x43  # LSX only


@dataclass(frozen=True, slots=True)
class Request:
    """Protocol request to send to speaker."""

    data: bytes

    @classmethod
    def get(cls, command_byte: int) -> Self:
        return cls(bytes([GET, command_byte, FLAG]))

    @classmethod
    def set_byte(cls, command_byte: int, value: int) -> Self:
        return cls(bytes([SET, command_byte, FLAG | 0x01, value]))

    @classmethod
    def set_string(cls, command_byte: int, value: str) -> Self:
        value_bytes = value.encode("utf-8") + b"\x00"
        length_flag = len(value_bytes) | FLAG
        return cls(bytes([SET, command_byte, length_flag]) + value_bytes)


@dataclass(frozen=True, slots=True)
class Response:
    """Parsed protocol response. Format: [RESPONSE, command, length_flag, ...payload...]."""

    raw: bytes
    command_byte: int
    payload: bytes

    @classmethod
    def parse(cls, data: bytes, expected_command: int | None = None) -> Self:
        """Parse response bytes using length-aware framing."""
        if not data:
            raise ProtocolError("Empty response")

        # Parse frames using length byte (handles 0x52 in payloads correctly)
        frames = cls._parse_frames(data)

        for raw, cmd, payload in frames:
            if raw == OK_RESPONSE:
                return cls(raw=raw, command_byte=0x11, payload=b"")
            if expected_command is None or cmd == expected_command:
                return cls(raw=raw, command_byte=cmd, payload=payload)

        raise ProtocolError(f"No matching response found in {data!r}")

    @staticmethod
    def _parse_frames(data: bytes) -> list[tuple[bytes, int, bytes]]:
        """Extract frames from response data. Returns list of (raw, command, payload)."""
        frames: list[tuple[bytes, int, bytes]] = []
        i = 0
        while i < len(data):
            # Look for RESPONSE marker
            if data[i] != RESPONSE:
                i += 1
                continue

            # Need at least 3 bytes for a valid frame
            if i + 3 > len(data):
                break

            # Check for OK_RESPONSE (special 3-byte response)
            if data[i : i + 3] == OK_RESPONSE:
                frames.append((OK_RESPONSE, 0x11, b""))
                i += 3
                continue

            # Normal response: [RESPONSE, command, length_flag, ...payload...]
            cmd = data[i + 1]
            length = data[i + 2] & 0x7F  # Clear high bit to get length

            # Extract frame
            frame_end = i + 3 + length
            if frame_end > len(data):
                break  # Incomplete frame

            payload = data[i + 3 : frame_end]
            raw = data[i:frame_end]
            frames.append((raw, cmd, payload))
            i = frame_end

        return frames

    @property
    def is_ok(self) -> bool:
        return self.raw == OK_RESPONSE

    @property
    def value_byte(self) -> int:
        if not self.payload:
            raise ProtocolError("Response has no payload")
        return self.payload[0]

    @property
    def value_string(self) -> str:
        data = self.payload.rstrip(b"\x00")
        return data.decode("utf-8", errors="replace")
