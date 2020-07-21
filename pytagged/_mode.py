from enum import Enum


class Mode(Enum):
    """Enum for PyTagged cli mode
    """
    DEFAULT = 0
    PRINTONLY = 1
    BENCHMARK = 2