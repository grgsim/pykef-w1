from pykef_w1.enums import BassExtension, Orientation, Source, StandbyTime, SubPolarity
from pykef_w1.models import (
    EQ_DESK_DB,
    EQ_HIGH_PASS_HZ,
    EQ_SUB_GAIN_DB,
    EQ_TREBLE_DB,
    EqMode,
    SpeakerState,
    VolumeLimitState,
    VolumeState,
)


class TestSpeakerState:
    """Tests for SpeakerState dataclass."""

    def test_from_raw_wifi_on(self) -> None:
        """Test decoding WiFi source, powered on."""
        state = SpeakerState.from_raw(0x02)
        assert state.source == Source.WIFI
        assert state.is_on is True
        assert state.standby_time == StandbyTime.MINUTES_20
        assert state.orientation == Orientation.NORMAL

    def test_from_raw_bluetooth_off(self) -> None:
        """Test decoding Bluetooth source, powered off."""
        state = SpeakerState.from_raw(0x89)  # BT (9) + power off (0x80)
        assert state.source == Source.BLUETOOTH
        assert state.is_on is False

    def test_from_raw_optical_60min_inverted(self) -> None:
        """Test decoding Optical, 60min standby, inverted orientation."""
        # Source 11 (0x0B) + standby 60min (0x10) + inverted (0x40) = 0x5B
        state = SpeakerState.from_raw(0x5B)
        assert state.source == Source.OPTICAL
        assert state.is_on is True
        assert state.standby_time == StandbyTime.MINUTES_60
        assert state.orientation == Orientation.INVERTED

    def test_roundtrip(self) -> None:
        """Test encoding and decoding produces same state."""
        original = SpeakerState(
            source=Source.OPTICAL,
            is_on=True,
            standby_time=StandbyTime.MINUTES_60,
            orientation=Orientation.INVERTED,
        )
        encoded = original.to_raw()
        decoded = SpeakerState.from_raw(encoded)
        assert decoded == original

    def test_roundtrip_powered_off(self) -> None:
        """Test roundtrip with speaker powered off."""
        original = SpeakerState(
            source=Source.AUX,
            is_on=False,
            standby_time=StandbyTime.NEVER,
            orientation=Orientation.NORMAL,
        )
        encoded = original.to_raw()
        decoded = SpeakerState.from_raw(encoded)
        assert decoded == original


class TestVolumeState:
    """Tests for VolumeState dataclass."""

    def test_unmuted(self) -> None:
        """Test decoding unmuted volume."""
        state = VolumeState.from_raw(50)
        assert state.volume == 50
        assert state.is_muted is False

    def test_muted(self) -> None:
        """Test decoding muted volume."""
        state = VolumeState.from_raw(178)  # 50 + 128
        assert state.volume == 50
        assert state.is_muted is True

    def test_roundtrip_unmuted(self) -> None:
        """Test roundtrip unmuted."""
        original = VolumeState(volume=75, is_muted=False)
        encoded = original.to_raw()
        decoded = VolumeState.from_raw(encoded)
        assert decoded == original

    def test_roundtrip_muted(self) -> None:
        """Test roundtrip muted."""
        original = VolumeState(volume=30, is_muted=True)
        encoded = original.to_raw()
        decoded = VolumeState.from_raw(encoded)
        assert decoded == original


class TestEqMode:
    """Tests for EqMode dataclass."""

    def test_from_raw_basic(self) -> None:
        """Test decoding basic EQ mode."""
        # Desk mode only: bit 0 = 1
        state = EqMode.from_raw(0x01)
        assert state.desk_mode is True
        assert state.wall_mode is False
        assert state.phase_correction is False
        assert state.high_pass is False
        assert state.bass_extension == BassExtension.STANDARD
        assert state.sub_polarity == SubPolarity.NORMAL

    def test_from_raw_complex(self) -> None:
        """Test decoding complex EQ mode."""
        # Wall + phase + highpass + extra bass + inverted polarity
        # bits: 0=0, 1=1, 2=1, 3=1, 4-5=01, 6=1 = 0b01011110 = 0x5E
        state = EqMode.from_raw(0x5E)
        assert state.desk_mode is False
        assert state.wall_mode is True
        assert state.phase_correction is True
        assert state.high_pass is True
        assert state.bass_extension == BassExtension.EXTRA
        assert state.sub_polarity == SubPolarity.INVERTED

    def test_roundtrip(self) -> None:
        """Test encoding and decoding produces same state."""
        original = EqMode(
            desk_mode=True,
            wall_mode=False,
            phase_correction=True,
            high_pass=False,
            bass_extension=BassExtension.LESS,
            sub_polarity=SubPolarity.INVERTED,
        )
        encoded = original.to_raw()
        # Note: to_raw() sets bit 7 for SET, so we need to mask it off for from_raw
        decoded = EqMode.from_raw(encoded & 0x7F)
        assert decoded == original


class TestVolumeLimitState:
    """Tests for VolumeLimitState dataclass."""

    def test_disabled(self) -> None:
        """Test decoding disabled volume limit."""
        state = VolumeLimitState.from_raw(100)
        assert state.limit == 100
        assert state.enabled is False

    def test_enabled(self) -> None:
        """Test decoding enabled volume limit."""
        state = VolumeLimitState.from_raw(180)  # 52 + 128
        assert state.limit == 52
        assert state.enabled is True

    def test_roundtrip(self) -> None:
        """Test roundtrip."""
        original = VolumeLimitState(limit=80, enabled=True)
        encoded = original.to_raw()
        decoded = VolumeLimitState.from_raw(encoded)
        assert decoded == original


class TestEQSettings:
    """Tests for EQSettings encode/decode."""

    def test_desk_db_decode(self) -> None:
        """Test decoding desk dB value."""
        # Raw 0x86 = index 6, value = -6.0 + 0.5*6 = -3.0 dB
        assert EQ_DESK_DB.decode(0x86) == -3.0

    def test_desk_db_encode(self) -> None:
        """Test encoding desk dB value."""
        # -3.0 dB = index 6 = 6 | 0x80 = 0x86
        assert EQ_DESK_DB.encode(-3.0) == 0x86

    def test_treble_decode(self) -> None:
        """Test decoding treble value."""
        # Raw 0x84 = index 4, value = -2.0 + 0.5*4 = 0.0 dB
        assert EQ_TREBLE_DB.decode(0x84) == 0.0

    def test_treble_encode(self) -> None:
        """Test encoding treble value."""
        # +1.0 dB = index 6 = 6 | 0x80 = 0x86
        assert EQ_TREBLE_DB.encode(1.0) == 0x86

    def test_high_pass_decode(self) -> None:
        """Test decoding high pass frequency."""
        # Raw 0x86 = index 6, value = 50 + 5*6 = 80 Hz
        assert EQ_HIGH_PASS_HZ.decode(0x86) == 80.0

    def test_sub_gain_decode(self) -> None:
        """Test decoding sub gain value."""
        # Raw 0x8A = index 10, value = -10 + 1*10 = 0 dB
        assert EQ_SUB_GAIN_DB.decode(0x8A) == 0.0

    def test_clamp_above_max(self) -> None:
        """Test clamping value above max."""
        # Desk dB max is 0.0, encoding 5.0 should clamp to 0.0
        encoded = EQ_DESK_DB.encode(5.0)
        decoded = EQ_DESK_DB.decode(encoded)
        assert decoded == 0.0

    def test_clamp_below_min(self) -> None:
        """Test clamping value below min."""
        # Desk dB min is -6.0, encoding -10.0 should clamp to -6.0
        encoded = EQ_DESK_DB.encode(-10.0)
        decoded = EQ_DESK_DB.decode(encoded)
        assert decoded == -6.0
