from dataclasses import dataclass
from typing import Self

from .enums import BassExtension, Orientation, Source, StandbyTime, SubPolarity


@dataclass(frozen=True, slots=True)
class SpeakerState:
    """Speaker state. Bits: 0-3=source, 4-5=standby, 6=orientation, 7=power(inverted)."""

    source: Source
    standby_time: StandbyTime
    orientation: Orientation
    is_on: bool

    @classmethod
    def from_raw(cls, raw: int) -> Self:
        source = Source(raw & 0x0F)
        standby_time = StandbyTime((raw >> 4) & 0x03)
        orientation = Orientation((raw >> 6) & 0x01)
        is_on = not bool((raw >> 7) & 0x01)
        return cls(source=source, standby_time=standby_time, orientation=orientation, is_on=is_on)

    def to_raw(self) -> int:
        value = self.source.value
        value |= self.standby_time.value << 4
        value |= self.orientation.value << 6
        value |= (not self.is_on) << 7
        return value


@dataclass(frozen=True, slots=True)
class VolumeState:
    """Volume state. Bits: 0-6=volume(0-100), 7=muted."""

    volume: int
    is_muted: bool

    @classmethod
    def from_raw(cls, raw: int) -> Self:
        return cls(volume=raw & 0x7F, is_muted=bool((raw >> 7) & 0x01))

    def to_raw(self) -> int:
        value = self.volume & 0x7F
        value |= self.is_muted << 7
        return value


@dataclass(frozen=True, slots=True)
class EqMode:
    """EQ mode. Bits: 0=desk, 1=wall, 2=phase, 3=highpass, 4-5=bass_ext, 6=sub_polarity."""

    desk_mode: bool
    wall_mode: bool
    phase_correction: bool
    high_pass: bool
    bass_extension: BassExtension
    sub_polarity: SubPolarity

    @classmethod
    def from_raw(cls, raw: int) -> Self:
        return cls(
            desk_mode=bool(raw & 0x01),
            wall_mode=bool((raw >> 1) & 0x01),
            phase_correction=bool((raw >> 2) & 0x01),
            high_pass=bool((raw >> 3) & 0x01),
            bass_extension=BassExtension((raw >> 4) & 0x03),
            sub_polarity=SubPolarity.INVERTED if (raw >> 6) & 0x01 else SubPolarity.NORMAL,
        )

    def to_raw(self) -> int:
        value = 0x80  # Bit 7 required for SET
        if self.desk_mode:
            value |= 0x01
        if self.wall_mode:
            value |= 0x02
        if self.phase_correction:
            value |= 0x04
        if self.high_pass:
            value |= 0x08
        value |= self.bass_extension.value << 4
        if self.sub_polarity == SubPolarity.INVERTED:
            value |= 0x40
        return value


@dataclass(frozen=True, slots=True)
class VolumeLimitState:
    """Volume limit. Bits: 0-6=limit(0-100), 7=enabled."""

    limit: int
    enabled: bool

    @classmethod
    def from_raw(cls, raw: int) -> Self:
        return cls(limit=raw & 0x7F, enabled=bool((raw >> 7) & 0x01))

    def to_raw(self) -> int:
        value = self.limit & 0x7F
        if self.enabled:
            value |= 0x80
        return value


@dataclass(frozen=True, slots=True)
class EQSettings:
    """EQ parameter config.

    Protocol uses bit 7 as a "value present" flag, so actual value is in bits 0-6.
    Decode: clear bit 7 (XOR 0x80) to get index, then convert to display value.
    Encode: convert to index, then set bit 7 (OR 0x80).
    """

    name: str
    command: int
    min_value: float
    max_value: float
    step: float
    unit: str

    def decode(self, raw: int) -> float:
        index = raw ^ 0x80
        return self.min_value + (self.step * index)

    def encode(self, value: float) -> int:
        clamped = max(self.min_value, min(self.max_value, value))
        index = int(round((clamped - self.min_value) / self.step))
        return index | 0x80


# Pre-defined EQ settings
EQ_DESK_DB = EQSettings("desk_db", 0x28, -6.0, 0.0, 0.5, "dB")
EQ_WALL_DB = EQSettings("wall_db", 0x29, -6.0, 0.0, 0.5, "dB")
EQ_TREBLE_DB = EQSettings("treble_db", 0x2A, -2.0, 2.0, 0.5, "dB")
EQ_HIGH_PASS_HZ = EQSettings("high_pass_hz", 0x2B, 50.0, 120.0, 5.0, "Hz")
EQ_SUB_OUT_HZ = EQSettings("sub_out_hz", 0x2C, 40.0, 250.0, 5.0, "Hz")
EQ_SUB_GAIN_DB = EQSettings("sub_gain_db", 0x2D, -10.0, 10.0, 1.0, "dB")
