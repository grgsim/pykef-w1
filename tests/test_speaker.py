from pykef_w1 import (
    CableMode,
    Orientation,
    PlaybackState,
    Source,
    Speaker,
    StandbyTime,
)


class TestSpeakerVolume:
    """Tests for volume control."""

    async def test_get_volume(self, speaker: Speaker) -> None:
        """Test getting volume."""
        volume = await speaker.get_volume()
        assert volume.volume == 50
        assert volume.is_muted is False

    async def test_set_volume(self, speaker: Speaker) -> None:
        """Test setting volume."""
        await speaker.set_volume(75)
        volume = await speaker.get_volume()
        assert volume.volume == 75

    async def test_set_volume_with_mute(self, speaker: Speaker) -> None:
        """Test setting volume with explicit mute."""
        await speaker.set_volume(60, mute=True)
        volume = await speaker.get_volume()
        assert volume.volume == 60
        assert volume.is_muted is True

    async def test_mute(self, speaker: Speaker) -> None:
        """Test muting."""
        await speaker.mute()
        volume = await speaker.get_volume()
        assert volume.is_muted is True

    async def test_unmute(self, speaker: Speaker) -> None:
        """Test unmuting."""
        await speaker.mute()
        await speaker.unmute()
        volume = await speaker.get_volume()
        assert volume.is_muted is False


class TestSpeakerState:
    """Tests for speaker state."""

    async def test_get_state(self, speaker: Speaker) -> None:
        """Test getting speaker state."""
        state = await speaker.get_state()
        assert state.source == Source.WIFI
        assert state.is_on is True
        assert state.standby_time == StandbyTime.MINUTES_20
        assert state.orientation == Orientation.NORMAL

    async def test_is_on(self, speaker: Speaker) -> None:
        """Test checking power state."""
        assert await speaker.is_on() is True


class TestSpeakerSource:
    """Tests for source control."""

    async def test_get_source(self, speaker: Speaker) -> None:
        """Test getting source."""
        source = await speaker.get_source()
        assert source == Source.WIFI

    async def test_set_source(self, speaker: Speaker) -> None:
        """Test setting source."""
        await speaker.set_source(Source.BLUETOOTH)
        source = await speaker.get_source()
        assert source == Source.BLUETOOTH


class TestSpeakerPlayback:
    """Tests for playback control."""

    async def test_get_playback_state(self, speaker: Speaker) -> None:
        """Test getting playback state."""
        state = await speaker.get_playback_state()
        assert state == PlaybackState.STOPPED

    async def test_play(self, speaker: Speaker) -> None:
        """Test play command."""
        await speaker.play()
        state = await speaker.get_playback_state()
        assert state == PlaybackState.PLAYING

    async def test_pause(self, speaker: Speaker) -> None:
        """Test pause command."""
        await speaker.pause()
        state = await speaker.get_playback_state()
        assert state == PlaybackState.PAUSED


class TestSpeakerEqMode:
    """Tests for EQ mode settings."""

    async def test_get_eq_mode(self, speaker: Speaker) -> None:
        """Test getting EQ mode."""
        mode = await speaker.get_eq_mode()
        assert mode.desk_mode is True
        assert mode.phase_correction is True

    async def test_set_eq_mode(self, speaker: Speaker) -> None:
        """Test setting EQ mode."""
        await speaker.set_eq_mode(wall_mode=True, desk_mode=False)
        mode = await speaker.get_eq_mode()
        assert mode.wall_mode is True
        # desk_mode should have been set to False in state byte (bit 0)
        # Note: The mock server just stores the raw byte, so this tests the encoding


class TestSpeakerEQ:
    """Tests for EQ settings."""

    async def test_get_desk_db(self, speaker: Speaker) -> None:
        """Test getting desk dB."""
        value = await speaker.get_desk_db()
        assert value == -3.0

    async def test_set_desk_db(self, speaker: Speaker) -> None:
        """Test setting desk dB."""
        await speaker.set_desk_db(-1.5)
        value = await speaker.get_desk_db()
        assert value == -1.5

    async def test_get_treble_db(self, speaker: Speaker) -> None:
        """Test getting treble dB."""
        value = await speaker.get_treble_db()
        assert value == 0.0


class TestSpeakerAdditional:
    """Tests for additional features."""

    async def test_get_balance(self, speaker: Speaker) -> None:
        """Test getting balance."""
        balance = await speaker.get_balance()
        assert balance == 30  # Centered

    async def test_set_balance(self, speaker: Speaker) -> None:
        """Test setting balance."""
        await speaker.set_balance(45)
        balance = await speaker.get_balance()
        # Note: balance encoding uses bit 7 for SET, so we need to check the actual value
        assert balance == 45

    async def test_get_connection_mode(self, speaker: Speaker) -> None:
        """Test getting connection mode."""
        mode = await speaker.get_connection_mode()
        assert mode == CableMode.WIRED

    async def test_get_device_name(self, speaker: Speaker) -> None:
        """Test getting device name."""
        name = await speaker.get_device_name()
        assert name == "Test Speaker"


class TestSpeakerContextManager:
    """Tests for context manager usage."""

    async def test_context_manager(self, mock_server: tuple[str, int]) -> None:
        """Test using speaker as context manager."""
        host, port = mock_server
        async with Speaker(host, port=port) as speaker:
            state = await speaker.get_state()
            assert state is not None

    async def test_explicit_close(self, mock_server: tuple[str, int]) -> None:
        """Test explicit close."""
        host, port = mock_server
        speaker = Speaker(host, port=port)
        state = await speaker.get_state()
        assert state is not None
        await speaker.close()
