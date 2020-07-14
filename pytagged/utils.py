from typing import Iterable


def print_raw_lines(lines: Iterable[str]):
    for i, ln in enumerate(lines):
        print(f"|{i:3}| {repr(ln)}")
