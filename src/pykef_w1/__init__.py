from importlib.metadata import version

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
from .exceptions import (
    CommandError,
    ConnectionError,
    KefError,
    ProtocolError,
)
from .models import (
    EqMode,
    SpeakerState,
    VolumeLimitState,
    VolumeState,
)
from .speaker import Speaker

__version__ = version("pykef-w1")

__all__ = [
    # Main class
    "Speaker",
    # State models
    "SpeakerState",
    "VolumeState",
    "EqMode",
    "VolumeLimitState",
    # Enums
    "Source",
    "PlaybackState",
    "PlaybackCommand",
    "StandbyTime",
    "Orientation",
    "BassExtension",
    "SubPolarity",
    "CableMode",
    # Exceptions
    "KefError",
    "ConnectionError",
    "ProtocolError",
    "CommandError",
]
