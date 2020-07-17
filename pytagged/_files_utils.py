import os
import fnmatch as _fnmatch
from typing import Sequence, Generator, Callable


def fnmatch(path: str, patterns: Sequence[str]) -> bool:
    """Wraps fnmatch to match against a sequence of patterns.
    Returns True is path is matched against any pattern.
    False otherwise
    """
    return any(_fnmatch.fnmatch(path, ptrn) for ptrn in patterns)


def match_path(path: str, patterns: Sequence[str]) -> bool:
    """Test if the path matches against any one of the patterns

    Args:
        path (str): path to file/directory
        patterns (Sequence[str]): patterns to match against

    Returns:
        bool: True if path matches any pattern. False otherwise
    """
    if not patterns:
        return False

    # match basename
    basename = os.path.basename(path)
    if basename not in ('**', "*"):
        return fnmatch(basename, patterns)

    # match abspath
    abs_path = os.path.abspath(path)
    return fnmatch(abs_path, patterns)


def filepaths_from_path(
        path: str,
        is_excluded: Callable[[str], bool]) -> Generator[str, str, None]:
    """Generates filtered paths to files from a path.

    Args:
        path (str): Given path
        is_excluded (Callable[[str], bool]): Callable that takes a path and returns
            a bool. If True, exclude the path, else yield it.

    Yields:
        Generator[str, str, None]: Generator of paths to files
    """
    if is_excluded(path):
        return

    if os.path.isdir(path):
        for root, subdirs, fnames in os.walk(path):
            if is_excluded(root):
                # if root is excluded, no need to walk the subdirs
                subdirs[:] = []
                continue

            for d in subdirs:
                # remove excluded directory
                if is_excluded(d):
                    subdirs.remove(d)

            for f in fnames:
                joined = os.path.join(root, f)
                if not is_excluded(joined):
                    yield joined
    else:
        yield path
