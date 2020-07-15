import argparse
from enum import Enum
import statistics
import sys
import textwrap
from os import path
from shutil import get_terminal_size
from pathlib import Path
from tempfile import TemporaryFile
from typing import Sequence, IO, Tuple

from pytagged import pytagged
from pytagged.utils import print_raw_lines, pretty_print_title, time_fn_only

PY_EXT = '.py'


class Mode(Enum):
    """Enum for PyTagged cli mode
    """
    DEFAULT = 0
    PRINTONLY = 1
    BENCHMARK = 2
    VERBOSE = 3


def printonly_single_file(io: IO, fname:str, *tags: str):
    newlines = pytagged.get_newlines(io, *tags)
    pretty_print_title(fname, span=True)
    print_raw_lines(newlines)
    pretty_print_title("EOF", span=True)


def printonly_files(io_seq: Sequence[Tuple[str, IO]], *tags: str):
    print_raw = print_raw_lines
    print_title = pretty_print_title
    get_newlines = pytagged.get_newlines

    def print_fn(io: IO):
        newlines = get_newlines(io, *tags)
        print_raw(newlines)

    for fname, io in io_seq:
        print_title(fname, span=True)
        print_fn(io)
        print_title("EOF", span=True)
        print('')


def benchmark_single_file(io: IO, fname: str, num_runs: int, *tags: str):
    file_content_og = io.read()
    io.seek(0)
    num_lines = len(list(io))
    io.seek(0)

    # wrap modify_single_file in time_fn_only
    timer = time_fn_only(modify_single_file)
    elapsed_times = []
    for _ in range(num_runs):
        # time modifying the file
        et = timer(io, *tags)
        elapsed_times.append(et)

        # restore the file content
        io.seek(0)
        io.truncate()
        io.write(file_content_og)
        io.seek(0)

    heading = "PERFORMANCE REPORT"
    footer = "END_REPORT"
    avg_run = statistics.mean(elapsed_times) * 1000
    median_run = statistics.median(elapsed_times) * 1000
    num_runs = len(elapsed_times)
    avg_per_line = sum(elapsed_times) / (num_runs * 1000) * 1000

    stats = {
        "Average time": avg_run,
        "Median time": median_run,
        "Average time per line": avg_per_line,
    }

    misc = {
        "File": fname,
        "Number of runs": num_runs,
        "Number of lines": num_lines,
    }

    pretty_print_title(heading, span=True)
    width = get_terminal_size().columns // 5

    for k, v in misc.items():
        print(f"{k:{width}} {v:>{width}}")
    for k, v in stats.items():
        print(f"{k:{width}} {v:>{width - 2}.4f}ms")

    pretty_print_title(footer, span=True)


def benchmark_files(io_seq: Sequence[Tuple[str, IO]], num_runs: int, *tags: str):
    og_contents = {}
    total_lines = 0
    for name, io in io_seq:
        og_contents[name] = io.read()
        io.seek(0)
        total_lines += len(list(io))
        io.seek(0)

    # wrap modify_single_file in time_fn_only
    timer = time_fn_only(modify_files)
    elapsed_times = []
    for _ in range(num_runs):
        # time modifying files
        et = timer(io_seq, *tags)
        elapsed_times.append(et)

        for name, io in io_seq:
            io.seek(0)
            io.truncate()
            io.write(og_contents[name])
            io.seek(0)

    heading = "PERFORMANCE REPORT"
    footer = "END_REPORT"
    avg_run = statistics.mean(elapsed_times) * 1000
    median_run = statistics.median(elapsed_times) * 1000
    num_runs = len(elapsed_times)
    avg_per_line = sum(elapsed_times) / (num_runs * 1000) * 1000

    stats = {
        "Average time": avg_run,
        "Median time": median_run,
        "Average time per line": avg_per_line,
    }
    misc = {
        "Number of files": len(og_contents.keys()),
        "Number of runs": num_runs,
        "Number of lines": total_lines
    }

    pretty_print_title(heading, span=True)
    width = get_terminal_size().columns // 5

    for k, v in misc.items():
        print(f"{k:{width}} {v:>{width}}")
    for k, v in stats.items():
        print(f"{k:{width}} {v:>{width - 2}.4f}ms")

    pretty_print_title(footer, span=True)


def modify_single_file_verbose(io: IO, fname: str, *tags: str):
    newlines = pytagged.get_newlines(io, *tags)
    io.seek(0)
    io.truncate()
    io.writelines(newlines)
    pretty_print_title(fname, span=True)
    print_raw_lines(newlines)
    pretty_print_title("EOF", span=True)


def modify_files_verbose(io_seq: Sequence[Tuple[str, IO]], *tags: str):
    print_raw = print_raw_lines
    print_title = pretty_print_title
    get_newlines = pytagged.get_newlines
    raw_str = []
    fnames = []

    def mod_file(f: IO):
        newlines = get_newlines(f, *tags)
        f.seek(0)
        f.truncate()
        f.writelines(newlines)
        raw_str.append(newlines)

    for fname, f_io in io_seq:
        mod_file(f_io)
        fnames.append(fname)

    for i, lines in enumerate(raw_str):
        print_title(fnames[i], span=True)
        print_raw(lines)
        print_title("EOF", span=True)
        print('')


def modify_single_file(io: IO, *tags: str):
    newlines = pytagged.get_newlines(io, *tags)
    io.seek(0)
    io.truncate()
    io.writelines(newlines)


def modify_files(io_seq: Sequence[Tuple[str, IO]], *tags: str):
    get_newlines = pytagged.get_newlines

    def mod_file(f: IO):
        newlines = get_newlines(f, *tags)
        f.seek(0)
        f.truncate()
        f.writelines(newlines)
    for i in io_seq:
        mod_file(i[1])


def copy_to_temp_file(pathobj: Path) -> IO:
    with pathobj.open() as f:
        src = f.read()

    # write newlines to temp file
    # pathstr, ext = path.splitext(str(pathobj))
    # ext = ".tmp"

    temp_file = TemporaryFile(mode="w+")
    temp_file.write(src)
    temp_file.seek(0)
    return temp_file


class NonPythonFileError(Exception):
    """Raise this if not '.py' extension
    """
    pass


def main():
    arg_parser = argparse.ArgumentParser(
        description="Comment out tagged code in your python code",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter)

    # required args
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

    arg_parser.add_argument("-t", "--tags",
                            type=str,
                            nargs='*',
                            required=True,
                            help=textwrap.dedent("""\
                            one or more 'tags', this tells the program
                            what to comment out.\n \n"""))

    # optional args
    arg_parser.add_argument("-h", "--help",
                            action="store_true",
                            help="Show help messages and exit.\n \n")

    modes = arg_parser.add_mutually_exclusive_group()
    modes.add_argument("-b", "--benchmark",
                       type=int,
                       help=textwrap.dedent("""\
                            Number of benchmark runs, if this is supplied
                            the program will run for N times, and print out
                            some performance statistics. Note that after PyTagged
                            is done, files will be restored to their original
                            content. Will also ignore the -v flag.\n \n"""))

    modes.add_argument("-p", "--printonly",
                       action="store_true",
                       help=textwrap.dedent("""\
                            Print only mode, if this flag is equivalent to the -v
                            flag but the program will not modify file(s).\n \n"""))

    modes.add_argument("-v", "--verbose",
                       action="store_true",
                       help=textwrap.dedent("""\
                            Verbose mode, if this flag is used,
                            the program will print out, line by line,
                            the raw string of the modified file."""))

    args = arg_parser.parse_args()

    if args.help:
        arg_parser.print_help()
        sys.exit(0)

    mode_int = 0
    if args.printonly:
        mode_int = 1
    elif args.benchmark:
        mode_int = 2
    elif args.verbose:
        mode_int = 3

    run_mode = Mode(mode_int)

    path_str = args.path
    path_obj = Path(path_str)
    tags = args.tags

    # block: develop
    print("PyTagged running in dev mode")
    print(f"cli mode: {run_mode.name.lower()}, using tags: {', '.join(tags)}")
    print('')
    # end

    try:
        if path_obj.is_file():
            _, ext = path.splitext(path_str)
            if ext and ext != PY_EXT:
                raise NonPythonFileError(f"{path_str} is not a python file")

            if run_mode is Mode.DEFAULT:
                file_io = path_obj.open('r+')
                modify_single_file(file_io, *tags)

            elif run_mode is Mode.PRINTONLY:
                file_io = path_obj.open()
                printonly_single_file(file_io, path_str, *tags)

            elif run_mode is Mode.BENCHMARK:
                benchmark_runs = args.benchmark
                file_io = copy_to_temp_file(path_obj)
                benchmark_single_file(file_io, path_str, benchmark_runs, *tags)

            elif run_mode is Mode.VERBOSE:
                file_io = path_obj.open('r+')
                modify_single_file_verbose(file_io, path_str, *tags)

            file_io.close()
            sys.exit(0)

        if path_obj.is_dir():
            py_paths = list(path_obj.glob("*.py"))
            if not py_paths:
                print(f"No .py files found in {path_str}")
                sys.exit(0)

            if run_mode is Mode.DEFAULT:
                io_seq = [(str(p), p.open("r+")) for p in py_paths]
                modify_files(io_seq, *tags)

            elif run_mode is Mode.PRINTONLY:
                io_seq = [(str(p), p.open()) for p in py_paths]
                printonly_files(io_seq, *tags)

            elif run_mode is Mode.BENCHMARK:
                # copy the src files to temp files
                run_num = args.benchmark
                io_seq = [(str(p), copy_to_temp_file(p)) for p in py_paths]
                benchmark_files(io_seq, run_num, *tags)

            elif run_mode is Mode.VERBOSE:
                io_seq = [(str(p), p.open("r+")) for p in py_paths]
                modify_files_verbose(io_seq, *tags)

            for i in io_seq:
                i[1].close()
            sys.exit(0)

    except (OSError, IOError, PermissionError, NonPythonFileError) as e:
        print(e)
        sys.exit(-1)
