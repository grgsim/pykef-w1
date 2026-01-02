class KefError(Exception):
    """Base exception for pykef-w1."""


class ConnectionError(KefError):
    """Connection-related errors (failed to connect, timeout, etc.)."""


class ProtocolError(KefError):
    """Protocol encoding/decoding errors."""


class CommandError(KefError):
    """Command execution failed."""
