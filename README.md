# pykef-w1

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Modern Python library for KEF LS50 Wireless and LSX speakers.

## Supported Speakers

- KEF LS50 Wireless (first generation)
- KEF LSX (first generation)

> **Note:** This library does not support LS50 Wireless II, LSX II, or other newer KEF models which use a different protocol.

## Protocol Documentation

See [docs/PROTOCOL.md](docs/PROTOCOL.md) for the complete protocol specification.

## Development

```bash
# Install dependencies
uv sync

# Run linter
uv run ruff check .

# Run type checker
uv run ty check
```

## License

[MIT](LICENSE)
