import argparse
import re
import sys
from os import path, get_terminal_size
from pathlib import Path
import statistics
import time
from typing import List, IO, Tuple

POUND = '#'
PY_EXT = '.py'
DEBUG_ANCHOR = "# debug"
BLOCK_START = "# block:"
BLOCK_END = "# end"
TRIPLE_QUOTE = '"""'


def comment_lines(lines: List[str], tag: str, *tags: str):
    tags_match_str = tag

    if len(tags) > 0:
        tags_match_str += '|' + '|'.join(tags)

    line_split_rgx = re.compile(r"^(?!\s*$)(\s*)(.+)")
    block_start_rgx = re.compile(rf"{BLOCK_START} ({tags_match_str})")
    triple_quote_rgx = re.compile(rf"{TRIPLE_QUOTE}")
    inline_rgx = re.compile(rf"^(?!{POUND}).*{POUND} ({tags_match_str})$")
    # monotonic_time = time.monotonic
    cur_block_start_idx = -1
    cur_triple_quote_start_idx = -1
    indices = set()
    block_pairs = []
    triple_quote_pairs = []
    matches = []

    # line_scan_st = monotonic_time()
    # inline_scan_dur = 0
    # split_line_dur = 0
    for i, ln in enumerate(lines):
        #st = monotonic_time()
        matched = line_split_rgx.search(ln)
        #split_line_dur += 1000 * (monotonic_time() - st)
        matches.append(matched)
        if not matched:
            continue
        non_whitespace = matched.group(2)

        #t = monotonic_time()
        if inline_rgx.search(non_whitespace):
            indices.add(i)
        #inline_scan_dur += 1000 * (monotonic_time() - st)

        if non_whitespace == BLOCK_END:
            block_pairs.append((cur_block_start_idx, i))
            cur_block_start_idx = -1
            continue

        if non_whitespace == TRIPLE_QUOTE:
            triple_quote_pairs.append((cur_triple_quote_start_idx, i))
            cur_triple_quote_start_idx = -1
            continue

        if block_start_rgx.match(non_whitespace):
            cur_block_start_idx = i
            continue

        if triple_quote_rgx.match(non_whitespace):
            cur_triple_quote_start_idx = i
            continue

    """ line_scan_dur = 1000 * (monotonic_time() - line_scan_st)
    print(f"Time taken for scanning lines & computing indices: {line_scan_dur:.2f} ms")
    print(f"Time taken for rgx splitting: {split_line_dur:.2f} ms")
    print(f"Time taken for inline rgx match: {inline_scan_dur:.2f} ms") """

    # update block indices
    for idx in block_pairs:
        start, end = idx
        if start == -1:
            continue
        indices |= {j for j in range(start + 1, end)}

    # remove triple quote block indices
    for idx in triple_quote_pairs:
        start, end = idx
        if start == -1:
            continue
        indices -= {j for j in range(start, end+1)}

    for i in indices:
        matched = matches[i]
        if matched:
            lines[i] = matched.expand(r"\g<1># \g<2>\n")


def write_temp_file(pathobj: Path, lines: List[str]):
    pathstr, ext = path.splitext(str(pathobj))
    with open(f"{pathstr}_tmp{ext}", 'w') as f:
        f.writelines(lines)


def time_comment_lines(lines: List[str], *tags: str, num_runs: int = 1) -> List[float]:
    times = []
    timer = time.monotonic
    for _ in range(num_runs):
        start = timer()
        comment_lines(lines, *tags)
        times.append(timer() - start)
    return times


def report_performance_single_file(filename: str, num_lines: int, data: List[float]):
    terminal_width = get_terminal_size().columns
    heading = "PERFORMANCE REPORT"
    footer = "END_REPORT"
    heading_marker_width = (terminal_width - len(heading)) // 2
    footer_marker_width = (terminal_width - len(footer)) // 2

    heading_left = '=' * heading_marker_width
    heading_right = '=' * (terminal_width - heading_marker_width - len(heading))
    footer_left = '=' * footer_marker_width
    footer_right = '=' * (terminal_width - footer_marker_width - len(footer))

    avg_run = statistics.mean(data) * 1000
    median_run = statistics.median(data) * 1000
    num_runs = len(data)
    avg_per_line = sum(data) / (num_runs * 1000) * 1000

    stats = {
        "Average time": avg_run,
        "Median time": median_run,
        "Average time per line": avg_per_line,
    }

    misc = {
        "File": filename,
        "Number of runs": num_runs,
        "Number of lines": num_lines,
    }

    print(f"{heading_left}{heading}{heading_right}")
    field_width = len(filename) + 10
    data_width = len(filename)

    for k, v in misc.items():
        print("{0:{fwidth}} {1:{dwidth}}".format(
            k, v,
            fwidth=field_width,
            dwidth=data_width
        ))


    for k, v in stats.items():
        print("{0:{fwidth}} {1:{dwidth}.4f}ms".format(
            k, v,
            fwidth=field_width,
            dwidth=data_width - 2
        ))

    print(f"{footer_left}{footer}{footer_right}")


class NonPythonFileError(Exception):
    pass


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Comment out marked code in your python code")
    arg_parser.add_argument("path",
                            type=str,
                            nargs='?',
                            default='.',
                            help="""path to python file(s),
                            if this is a directory, the program
                            will work on all files with the .py
                            extention within that directory.
                            Defaults to the current working dir.
                            """)
    arg_parser.add_argument("-t", "--tags",
                            type=str,
                            default="debug",
                            nargs='+',
                            help="""one or more 'tags', this tells the program
                            what to comment out. By default, the 'debug' tag
                            is used.
                            """)

    args = arg_parser.parse_args()
    try:
        path_str = args.path
        tags = args.tags
        _, ext = path.splitext(path_str)
        if ext and ext != PY_EXT:
            raise NonPythonFileError(f"{path_str} is not a pytho file")

        path_obj = Path(path_str)

        if path_obj.is_file():
            with path_obj.open() as f:
                lines = list(f)
            times = time_comment_lines(lines, *tags , num_runs=1000)
            report_performance_single_file(path_str, len(lines), times)

    except (OSError, IOError, PermissionError, NonPythonFileError) as e:
        print(e)
        sys.exit(-1)
