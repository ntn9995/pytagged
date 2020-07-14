import argparse
import statistics
import sys
import textwrap
import time
from os import get_terminal_size, path
from pathlib import Path
from typing import IO, List

from pytagged import pytagged
from pytagged.utils import print_raw_lines

PY_EXT = '.py'


def time_comment_lines(file: IO, *tags: str, num_runs: int = 1) -> List[float]:
    times = []
    timer = time.monotonic
    for _ in range(num_runs):
        start = timer()
        pytagged.get_newlines(file, *tags)
        times.append(timer() - start)
        file.seek(0)    # seek to start
    return times


def report_performance_single_file(filename: str, num_lines: int, data: List[float]):
    terminal_width = get_terminal_size().columns
    heading = "PERFORMANCE REPORT"
    footer = "END_REPORT"
    heading_marker_width = (terminal_width - len(heading)) // 2
    footer_marker_width = (terminal_width - len(footer)) // 2

    heading_left = '=' * heading_marker_width
    heading_right = '=' * \
        (terminal_width - heading_marker_width - len(heading))
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


def printonly_single_file(pathobj: Path, *tags: str):
    with pathobj.open() as f:
        newlines = pytagged.get_newlines(f, *tags)
        print_raw_lines(newlines)


def benchmark_single_file(pathobj: Path, *tags: str):
    with pathobj.open() as f:
        times = time_comment_lines(f, *tags, num_runs=benchmark_runs)
        report_performance_single_file(path_str, len(list(f)), times)


def tag_single_file_verbose(pathobj: Path, *tags: str):
    with pathobj.open("r+") as f:
        newlines = pytagged.get_newlines(f, *tags)
        f.seek(0)
        f.truncate()
        f.writelines(newlines)
        print_raw_lines(newlines)


def tag_single_file(pathobj: Path, *tags: str):
    with pathobj.open("r+") as f:
        newlines = pytagged.get_newlines(f, *tags)
        f.seek(0)
        f.truncate()
        f.writelines(newlines)


class NonPythonFileError(Exception):
    """Raise this if not '.py' extension
    """
    pass


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Comment out tagged code in your python code",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter)
    arg_parser.add_argument("path",
                            type=str,
                            nargs='?',
                            default='.',
                            help=textwrap.dedent("""\
                            path to python file(s),
                            if this is a directory, the program
                            will work on all files with the .py
                            extention within that directory.
                            Defaults to the current working dir.\n"""))

    arg_parser.add_argument("-h", "--help",
                            action="store_true",
                            help="Show help messages and exit.\n \n")

    arg_parser.add_argument("-t", "--tags",
                            type=str,
                            default="debug",
                            nargs='+',
                            help=textwrap.dedent("""\
                            one or more 'tags', this tells the program
                            what to comment out. By default, the 'debug'
                            tag is used.\n \n"""))

    arg_parser.add_argument("-b", "--benchmark",
                            type=int,
                            metavar='N',
                            help=textwrap.dedent("""\
                            Number of benchmark runs, if this is supplied
                            the program will run for N times, and print out
                            some performance statistics. Will also ignore the
                            -v flag.\n \n"""))

    arg_parser.add_argument("-p", "--printonly",
                            action="store_true",
                            help=textwrap.dedent("""\
                            Print only mode, if this flag is equivalent to the -v
                            flag but the program will not modify file(s).\n \n"""))

    arg_parser.add_argument("-v", "--verbose",
                            action="store_true",
                            help=textwrap.dedent("""\
                            Verbose mode, if this flag is used,
                            the program will print out, line by line,
                            the raw string of the modified file."""))

    args = arg_parser.parse_args()
    if args.help:
        arg_parser.print_help()
        sys.exit(0)

    try:
        path_str = args.path
        tags = args.tags
        benchmark_runs = args.benchmark
        printonly = args.printonly
        verbose = args.verbose
        _, ext = path.splitext(path_str)
        if ext and ext != PY_EXT:
            raise NonPythonFileError(f"{path_str} is not a pytho file")

        path_obj = Path(path_str)

        if path_obj.is_file():
            if benchmark_runs:
                benchmark_single_file(path_obj, *tags)
                sys.exit(0)

            if printonly:
                printonly_single_file(path_obj, *tags)
                sys.exit(0)

            if verbose:
                tag_single_file_verbose(path_obj, *tags)
                sys.exit(0)
            tag_single_file(path_obj, *tags)

    except (OSError, IOError, PermissionError, NonPythonFileError) as e:
        print(e)
        sys.exit(-1)
