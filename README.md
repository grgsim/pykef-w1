# pykef-w1

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Typed](https://img.shields.io/badge/typed-yes-blue.svg)](https://peps.python.org/pep-0561/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Modern Python library for KEF LS50 Wireless and LSX speakers.

## Features

- **Async-first** with synchronous wrapper for convenience
- **Zero dependencies** - pure Python 3.12+
- **Type-safe** with full type annotations
- **Complete API** - volume, source, EQ, playback, and more

## Supported Speakers

- KEF LS50 Wireless (first generation)
- KEF LSX (first generation)

> **Note:** This library does not support LS50 Wireless II, LSX II, or other newer KEF models which use a different protocol.

## Quick Start

### Async Usage

```python
import asyncio
from pykef_w1 import Speaker, Source

async def main():
    async with Speaker("192.168.1.19") as speaker:
        # Get current state
        state = await speaker.get_state()
        print(f"Source: {state.source.name}, Power: {'ON' if state.is_on else 'OFF'}")

        # Control volume
        volume = await speaker.get_volume()
        print(f"Volume: {volume.volume}%, Muted: {volume.is_muted}")

        await speaker.set_volume(50)

        # Change source
        await speaker.set_source(Source.BLUETOOTH)

asyncio.run(main())
```

### Synchronous Usage

```python
from pykef_w1 import Speaker

speaker = Speaker("192.168.1.19")

# Use the .sync property for synchronous calls
state = speaker.sync.get_state()
speaker.sync.set_volume(50)
speaker.sync.mute()
```

## API Reference

### Speaker Control

| Method | Description |
|--------|-------------|
| `get_state()` | Get source, power, standby time, orientation |
| `get_volume()` / `set_volume(level, mute=None)` | Volume control (0-100) |
| `mute()` / `unmute()` | Mute control |
| `get_source()` / `set_source(source)` | Input source |
| `is_on()` / `turn_on()` / `turn_off()` | Power control |

### Playback Control

| Method | Description |
|--------|-------------|
| `get_playback_state()` | Get playing/paused/stopped state |
| `play()` / `pause()` | Playback control |
| `next_track()` / `previous_track()` | Track navigation |

### EQ Settings

| Method | Description |
|--------|-------------|
| `get_eq_mode()` / `set_eq_mode(...)` | Desk mode, wall mode, phase correction, etc. |
| `get_desk_db()` / `set_desk_db(value)` | Desk mode EQ (-6.0 to 0.0 dB) |
| `get_wall_db()` / `set_wall_db(value)` | Wall mode EQ (-6.0 to 0.0 dB) |
| `get_treble_db()` / `set_treble_db(value)` | Treble trim (-2.0 to +2.0 dB) |
| `get_sub_gain_db()` / `set_sub_gain_db(value)` | Subwoofer level (-10 to +10 dB) |

### Additional Features

| Method | Description |
|--------|-------------|
| `get_balance()` / `set_balance(value)` | L/R balance (0-60, 30=center) |
| `get_device_name()` / `set_device_name(name)` | Speaker name |
| `get_standby_time()` / `set_standby_time(time)` | Auto-standby timeout |
| `get_orientation()` / `set_orientation(orient)` | L/R channel swap |
| `get_connection_mode()` | Cable mode (LSX only) |

## Connection Notes

- The TCP connection to the speaker is **exclusive** - only one client can connect at a time
- If the KEF Control app is connected, this library won't be able to connect
- The library auto-manages connections with a configurable keepalive timeout

## Protocol Documentation

See [docs/PROTOCOL.md](docs/PROTOCOL.md) for the complete protocol specification.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run type checker
uv run ty check
```

## License

[MIT](LICENSE)
