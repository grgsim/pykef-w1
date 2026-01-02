from enum import IntEnum, StrEnum


class Source(IntEnum):
    """Input source (bits 0-3 of 0x30)."""

    WIFI = 2
    BLUETOOTH = 9
    AUX = 10
    OPTICAL = 11
    PC = 12


class PlaybackState(IntEnum):
    """Playback state (0x31 GET)."""

    PAUSED = 128
    PLAYING = 129
    STOPPED = 132


class PlaybackCommand(IntEnum):
    """Playback control (0x31 SET)."""

    PAUSE = 128
    PLAY = 129
    NEXT = 130
    PREVIOUS = 131


class StandbyTime(IntEnum):
    """Auto-standby duration (bits 4-5 of 0x30)."""

    MINUTES_20 = 0
    MINUTES_60 = 1
    NEVER = 2


class Orientation(IntEnum):
    """Speaker L/R orientation (bit 6 of 0x30)."""

    NORMAL = 0
    INVERTED = 1


class BassExtension(IntEnum):
    """Bass extension (bits 4-5 of 0x27)."""

    STANDARD = 0
    EXTRA = 1
    LESS = 2


class SubPolarity(StrEnum):
    """Subwoofer polarity (bit 6 of 0x27)."""

    NORMAL = "+"
    INVERTED = "-"


class CableMode(IntEnum):
    """Inter-speaker connection (0x41, LSX only)."""

    WIRED = 1
    WIRELESS = 129
