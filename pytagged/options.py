"""Options typed namedtuple,
used as a common interface for both
cli args and config file options.
"""
from typing import List, NamedTuple, Optional

from pytagged._mode import Mode


class Options(NamedTuple):
    path: Optional[str] = None
    config_path: Optional[str] = None
    tags: Optional[List[str]] = None
    exclude: Optional[List[str]] = None
    extend_exclude: Optional[List[str]] = None

    # modes
    mode: Mode = Mode.DEFAULT       # mode is either default or something, never None
    benchmark_runs: Optional[int] = None
    verbosity: Optional[int] = None

    def update_if_not_none(self, other: "Options") -> "Options":
        """Returns a new Options instance with values from others.
        The value from 'other' will replace the originals if it is
        not None, otherwise the original value will be kept.

        Args:
            other (Options): the other Options instance
                whose values are used to updatd the original.

        Returns:
            Options: the new Options instance
        """
        merged = self._asdict()
        other_dict = other._asdict()
        for k, v in other_dict.items():
            if k in merged and v is not None and v:
                merged[k] = v

        return Options(**merged)
