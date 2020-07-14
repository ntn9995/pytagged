from os import get_terminal_size
from typing import Iterable


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
