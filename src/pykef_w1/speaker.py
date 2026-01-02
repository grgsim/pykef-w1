from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Self

from .connection import Connection, ConnectionConfig
from .enums import (
    BassExtension,
    CableMode,
    Orientation,
    PlaybackCommand,
    PlaybackState,
    Source,
    StandbyTime,
    SubPolarity,
)
from .exceptions import CommandError
from .models import (
    EQ_DESK_DB,
    EQ_HIGH_PASS_HZ,
    EQ_SUB_GAIN_DB,
    EQ_SUB_OUT_HZ,
    EQ_TREBLE_DB,
    EQ_WALL_DB,
    EqMode,
    SpeakerState,
    VolumeLimitState,
    VolumeState,
)
from .protocol import Command, Request

if TYPE_CHECKING:
    from ._sync import SyncWrapper


class Speaker:
    """Async API for KEF LS50 Wireless and LSX (gen 1). Sync access via .sync property."""

    def __init__(
        self,
        host: str,
        port: int = 50001,
        *,
        timeout: float = 2.0,
        keepalive: float = 1.0,
        max_retries: int = 3,
    ) -> None:
        self._config = ConnectionConfig(
            host=host,
            port=port,
            timeout=timeout,
            keepalive=keepalive,
            max_retries=max_retries,
        )
        self._connection = Connection(self._config)
        self._sync: SyncWrapper | None = None

    @property
    def host(self) -> str:
        return self._config.host

    @property
    def sync(self) -> SyncWrapper:
        if self._sync is None:
            from ._sync import SyncWrapper

            self._sync = SyncWrapper(self)
        return self._sync

    async def __aenter__(self) -> Self:
        await self._connection.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._connection.disconnect()

    async def close(self) -> None:
        await self._connection.disconnect()

    # --- Core State Operations ---

    async def get_state(self) -> SpeakerState:
        response = await self._connection.send(Request.get(Command.SOURCE))
        return SpeakerState.from_raw(response.value_byte)

    async def get_volume(self) -> VolumeState:
        response = await self._connection.send(Request.get(Command.VOLUME))
        return VolumeState.from_raw(response.value_byte)

    async def set_volume(self, volume: int, *, mute: bool | None = None) -> None:
        """Set volume (0-100). If mute is None, preserves current mute state."""
        if mute is None:
            current = await self.get_volume()
            mute = current.is_muted

        state = VolumeState(volume=max(0, min(100, volume)), is_muted=mute)
        response = await self._connection.send(Request.set_byte(Command.VOLUME, state.to_raw()))
        if not response.is_ok:
            raise CommandError("Failed to set volume")

    async def mute(self) -> None:
        current = await self.get_volume()
        await self.set_volume(current.volume, mute=True)

    async def unmute(self) -> None:
        current = await self.get_volume()
        await self.set_volume(current.volume, mute=False)

    # --- Source Control ---

    async def get_source(self) -> Source:
        state = await self.get_state()
        return state.source

    async def set_source(self, source: Source) -> None:
        current = await self.get_state()
        new_state = SpeakerState(
            source=source,
            is_on=current.is_on,
            standby_time=current.standby_time,
            orientation=current.orientation,
        )
        response = await self._connection.send(Request.set_byte(Command.SOURCE, new_state.to_raw()))
        if not response.is_ok:
            raise CommandError("Failed to set source")

    # --- Power Control ---

    async def is_on(self) -> bool:
        state = await self.get_state()
        return state.is_on

    async def turn_on(self) -> None:
        state = await self.get_state()
        if state.is_on:
            return
        new_state = SpeakerState(
            source=state.source,
            is_on=True,
            standby_time=state.standby_time,
            orientation=state.orientation,
        )
        response = await self._connection.send(Request.set_byte(Command.SOURCE, new_state.to_raw()))
        if not response.is_ok:
            raise CommandError("Failed to turn on")
        await self._wait_for_power(on=True)

    async def turn_off(self) -> None:
        state = await self.get_state()
        if not state.is_on:
            return
        new_state = SpeakerState(
            source=state.source,
            is_on=False,
            standby_time=state.standby_time,
            orientation=state.orientation,
        )
        response = await self._connection.send(Request.set_byte(Command.SOURCE, new_state.to_raw()))
        if not response.is_ok:
            raise CommandError("Failed to turn off")
        await self._wait_for_power(on=False)

    async def _wait_for_power(self, *, on: bool, timeout: float = 10.0) -> None:
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            if await self.is_on() == on:
                return
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Timeout waiting for power {'on' if on else 'off'}")

    # --- Playback Control ---

    async def get_playback_state(self) -> PlaybackState:
        response = await self._connection.send(Request.get(Command.PLAYBACK))
        return PlaybackState(response.value_byte)

    async def play(self) -> None:
        cmd = Request.set_byte(Command.PLAYBACK, PlaybackCommand.PLAY)
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to play")

    async def pause(self) -> None:
        cmd = Request.set_byte(Command.PLAYBACK, PlaybackCommand.PAUSE)
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to pause")

    async def next_track(self) -> None:
        cmd = Request.set_byte(Command.PLAYBACK, PlaybackCommand.NEXT)
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to skip track")

    async def previous_track(self) -> None:
        cmd = Request.set_byte(Command.PLAYBACK, PlaybackCommand.PREVIOUS)
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to go to previous track")

    # --- EQ Mode ---

    async def get_eq_mode(self) -> EqMode:
        response = await self._connection.send(Request.get(Command.EQ_MODE))
        return EqMode.from_raw(response.value_byte)

    async def set_eq_mode(
        self,
        *,
        desk_mode: bool | None = None,
        wall_mode: bool | None = None,
        phase_correction: bool | None = None,
        high_pass: bool | None = None,
        bass_extension: BassExtension | None = None,
        sub_polarity: SubPolarity | None = None,
    ) -> None:
        """Only specified parameters are changed."""
        current = await self.get_eq_mode()
        new_mode = EqMode(
            desk_mode=desk_mode if desk_mode is not None else current.desk_mode,
            wall_mode=wall_mode if wall_mode is not None else current.wall_mode,
            phase_correction=(
                phase_correction if phase_correction is not None else current.phase_correction
            ),
            high_pass=high_pass if high_pass is not None else current.high_pass,
            bass_extension=(
                bass_extension if bass_extension is not None else current.bass_extension
            ),
            sub_polarity=sub_polarity if sub_polarity is not None else current.sub_polarity,
        )
        response = await self._connection.send(Request.set_byte(Command.EQ_MODE, new_mode.to_raw()))
        if not response.is_ok:
            raise CommandError("Failed to set EQ mode")

    # --- EQ Settings ---

    async def get_desk_db(self) -> float:
        response = await self._connection.send(Request.get(Command.DESK_DB))
        return EQ_DESK_DB.decode(response.value_byte)

    async def set_desk_db(self, value: float) -> None:
        cmd = Request.set_byte(Command.DESK_DB, EQ_DESK_DB.encode(value))
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to set desk EQ")

    async def get_wall_db(self) -> float:
        response = await self._connection.send(Request.get(Command.WALL_DB))
        return EQ_WALL_DB.decode(response.value_byte)

    async def set_wall_db(self, value: float) -> None:
        cmd = Request.set_byte(Command.WALL_DB, EQ_WALL_DB.encode(value))
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to set wall EQ")

    async def get_treble_db(self) -> float:
        response = await self._connection.send(Request.get(Command.TREBLE_DB))
        return EQ_TREBLE_DB.decode(response.value_byte)

    async def set_treble_db(self, value: float) -> None:
        cmd = Request.set_byte(Command.TREBLE_DB, EQ_TREBLE_DB.encode(value))
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to set treble")

    async def get_high_pass_hz(self) -> float:
        response = await self._connection.send(Request.get(Command.HIGH_PASS_HZ))
        return EQ_HIGH_PASS_HZ.decode(response.value_byte)

    async def set_high_pass_hz(self, value: float) -> None:
        cmd = Request.set_byte(Command.HIGH_PASS_HZ, EQ_HIGH_PASS_HZ.encode(value))
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to set high pass")

    async def get_sub_out_hz(self) -> float:
        response = await self._connection.send(Request.get(Command.SUB_OUT_HZ))
        return EQ_SUB_OUT_HZ.decode(response.value_byte)

    async def set_sub_out_hz(self, value: float) -> None:
        cmd = Request.set_byte(Command.SUB_OUT_HZ, EQ_SUB_OUT_HZ.encode(value))
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to set sub out frequency")

    async def get_sub_gain_db(self) -> float:
        response = await self._connection.send(Request.get(Command.SUB_GAIN_DB))
        return EQ_SUB_GAIN_DB.decode(response.value_byte)

    async def set_sub_gain_db(self, value: float) -> None:
        cmd = Request.set_byte(Command.SUB_GAIN_DB, EQ_SUB_GAIN_DB.encode(value))
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to set sub gain")

    # --- Additional Features ---

    async def get_balance(self) -> int:
        """0=left, 30=center, 60=right."""
        response = await self._connection.send(Request.get(Command.BALANCE))
        return response.value_byte & 0x3F

    async def set_balance(self, value: int) -> None:
        """0=left, 30=center, 60=right."""
        clamped = max(0, min(60, value))
        response = await self._connection.send(Request.set_byte(Command.BALANCE, clamped | 0x80))
        if not response.is_ok:
            raise CommandError("Failed to set balance")

    async def get_volume_limit(self) -> VolumeLimitState:
        response = await self._connection.send(Request.get(Command.VOLUME_LIMIT))
        return VolumeLimitState.from_raw(response.value_byte)

    async def set_volume_limit(self, limit: int, *, enabled: bool = True) -> None:
        state = VolumeLimitState(limit=max(0, min(100, limit)), enabled=enabled)
        cmd = Request.set_byte(Command.VOLUME_LIMIT, state.to_raw())
        response = await self._connection.send(cmd)
        if not response.is_ok:
            raise CommandError("Failed to set volume limit")

    async def get_connection_mode(self) -> CableMode:
        response = await self._connection.send(Request.get(Command.CABLE_MODE))
        return CableMode(response.value_byte)

    async def get_device_name(self) -> str:
        response = await self._connection.send(Request.get(Command.DEVICE_NAME))
        return response.value_string

    async def set_device_name(self, name: str) -> None:
        response = await self._connection.send(Request.set_string(Command.DEVICE_NAME, name))
        if not response.is_ok:
            raise CommandError("Failed to set device name")

    async def get_standby_time(self) -> StandbyTime:
        state = await self.get_state()
        return state.standby_time

    async def set_standby_time(self, standby_time: StandbyTime) -> None:
        current = await self.get_state()
        new_state = SpeakerState(
            source=current.source,
            is_on=current.is_on,
            standby_time=standby_time,
            orientation=current.orientation,
        )
        response = await self._connection.send(Request.set_byte(Command.SOURCE, new_state.to_raw()))
        if not response.is_ok:
            raise CommandError("Failed to set standby time")

    async def get_orientation(self) -> Orientation:
        state = await self.get_state()
        return state.orientation

    async def set_orientation(self, orientation: Orientation) -> None:
        current = await self.get_state()
        new_state = SpeakerState(
            source=current.source,
            is_on=current.is_on,
            standby_time=current.standby_time,
            orientation=orientation,
        )
        response = await self._connection.send(Request.set_byte(Command.SOURCE, new_state.to_raw()))
        if not response.is_ok:
            raise CommandError("Failed to set orientation")
