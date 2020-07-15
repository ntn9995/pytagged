from os import get_terminal_size
import time
from typing import Iterable, Callable, Any, Tuple


def print_raw_lines(lines: Iterable[str]):
    for i, ln in enumerate(lines):
        print(f"|{i:3}| {repr(ln)}")


def pretty_print_title(title: str, width: int = 0,
                       padded_char: str = '=', span: bool = False):
    if width:
        print(f"{title:{padded_char}^{width}}")
        return

    width = len(title) + 20

    if span:
        try:
            term_width = get_terminal_size().columns
            width = term_width
        except OSError:
            pass
    print(f"{title:{padded_char}^{width}}")


def time_fn(fn: Callable) -> Callable:
    """Decorator/wrapper for to measure the execution of a callable.
    A function using this decorator will return a tuple whose
    first item is the result of the function itself, and the
    second item is the measured execution time.

    Args:
        fn (Callable): a callable whose execution time will be measured

    Returns:
        Callable: a wrapper that returns the result of the wrapped
            function and the measured execution time
    """
    def wrapper(*args: Any, **kwargs: Any) -> Tuple[Any, float]:

        st = time.monotonic()
        res = fn(*args, **kwargs)
        elapsed = time.monotonic() - st

        return res, elapsed
    return wrapper


def time_fn_only(fn: Callable) -> Callable:
    """Decorator/wrapper for to measure the execution of a callable.
    Unlike time_fn, a function using this decorator will only
    return the its measured execution time.

    Args:
        fn (Callable): a callable whose execution time will be measured

    Returns:
        Callable: a wrapper that returns the execution time of
            the wrapped function
    """
    def wrapper(*args: Any, **kwargs: Any) -> float:
        st = time.monotonic()
        fn(*args, **kwargs)
        return time.monotonic() - st

    return wrapper
