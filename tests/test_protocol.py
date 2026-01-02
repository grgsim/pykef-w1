import pytest

from pykef_w1.exceptions import ProtocolError
from pykef_w1.protocol import Command, Request, Response


class TestCommand:
    """Tests for Command class."""

    def test_get_command(self) -> None:
        """Test GET command encoding."""
        cmd = Request.get(Command.VOLUME)
        assert cmd.data == bytes([0x47, 0x25, 0x80])

    def test_get_command_source(self) -> None:
        """Test GET command for source."""
        cmd = Request.get(Command.SOURCE)
        assert cmd.data == bytes([0x47, 0x30, 0x80])

    def test_set_byte_command(self) -> None:
        """Test SET command with byte value."""
        cmd = Request.set_byte(Command.VOLUME, 50)
        assert cmd.data == bytes([0x53, 0x25, 0x81, 50])

    def test_set_string_command(self) -> None:
        """Test SET command with string value."""
        cmd = Request.set_string(Command.DEVICE_NAME, "Test")
        # Length = 5 (4 chars + null), so length_flag = 5 | 0x80 = 0x85
        assert cmd.data == bytes([0x53, 0x20, 0x85]) + b"Test\x00"

    def test_set_string_command_empty(self) -> None:
        """Test SET command with empty string."""
        cmd = Request.set_string(Command.DEVICE_NAME, "")
        # Length = 1 (just null), so length_flag = 1 | 0x80 = 0x81
        assert cmd.data == bytes([0x53, 0x20, 0x81, 0x00])


class TestResponse:
    """Tests for Response class."""

    def test_parse_ok_response(self) -> None:
        """Test parsing OK response."""
        data = bytes([0x52, 0x11, 0xFF])
        response = Response.parse(data)
        assert response.is_ok
        assert response.command_byte == 0x11

    def test_parse_get_response(self) -> None:
        """Test parsing GET response."""
        data = bytes([0x52, 0x25, 0x81, 0x32])
        response = Response.parse(data, expected_command=0x25)
        assert response.value_byte == 0x32
        assert not response.is_ok

    def test_parse_multiple_responses(self) -> None:
        """Test parsing concatenated responses."""
        # Sometimes speaker sends multiple responses concatenated
        data = bytes([0x52, 0x30, 0x81, 0x02, 0x52, 0x25, 0x81, 0x32])
        response = Response.parse(data, expected_command=0x25)
        assert response.value_byte == 0x32

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response raises error."""
        with pytest.raises(ProtocolError, match="Empty response"):
            Response.parse(b"")

    def test_parse_no_match(self) -> None:
        """Test parsing with no matching command raises error."""
        data = bytes([0x52, 0x30, 0x81, 0x02])
        with pytest.raises(ProtocolError, match="No matching response"):
            Response.parse(data, expected_command=0x25)

    def test_value_string(self) -> None:
        """Test extracting string value from response."""
        data = bytes([0x52, 0x20, 0x85]) + b"Test\x00"
        response = Response.parse(data, expected_command=0x20)
        assert response.value_string == "Test"

    def test_value_byte_no_payload(self) -> None:
        """Test value_byte with no payload raises error."""
        data = bytes([0x52, 0x11, 0xFF])
        response = Response.parse(data)
        with pytest.raises(ProtocolError, match="no payload"):
            _ = response.value_byte
