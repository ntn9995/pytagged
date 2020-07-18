import io
import statistics
import sys
import tempfile
import time
from shutil import get_terminal_size
from typing import (
    Callable, IO,
    Sequence, Optional,
    Iterable, Tuple, Union
)

from pytagged._mode import Mode
from pytagged import _files_utils
from pytagged import _utils
from pytagged import nline

# types
LineProg = Callable[[IO, Iterable[str]], Sequence[str]]
LineProgResult = Optional[Sequence[str]]
IOType = Union[IO, str]

# version control, cache, eggs & envs
# some of these are taken from the default
# that flake8 uses
DEFAULT_EXCLUDED_PATTERNS = [
    ".snv", "CVS", ".bzr", ".hg", ".git",
    "__pycache__", ".tox", ".eggs", "*.egg",
]
PY_EXT = '.py'


def run(mode: int,
        path: str,
        tags: Sequence[str],
        benchmark_runs: int = None,
        exclude_patterns: Sequence[str] = None):

    for i, tag in enumerate(tags):
        stripped = tag.strip()
        if not stripped:
            sys.stderr.write(f"Error: empty tag at {i}\n")
            sys.exit(-1)
        else:
            tags[i] = stripped

    mode_enum = Mode(mode)
    if not exclude_patterns:
        exclude_patterns = DEFAULT_EXCLUDED_PATTERNS

    # block: develop
    print("PyTagged running in dev mode")
    print(f"cli mode: {mode_enum.name.lower()}, using tags: {', '.join(tags)}")
    print(f"Using tags: {', '.join(tags)}")
    print(f"On path: {path}")
    print(f"excluding patterns: {', '.join(exclude_patterns)}")
    # end

    def exclude(pth: str) -> bool:
        return _files_utils.match_path(pth, exclude_patterns)

    gen_files = _files_utils.filepaths_from_path(path, is_excluded=exclude)
    files = [f for f in gen_files if f.endswith(PY_EXT)]

    if not files:
        print(f"Found no files matching pattern: {path}")
        sys.exit(0)

    # block: develop
    print(f"Collected {len(files)} files:")
    for f in files:
        print(f)
    # end

    # run modes
    if mode_enum is Mode.DEFAULT:
        process_files(files, tags, False)

    elif mode_enum is Mode.PRINTONLY:
        process_files_printonly(files, tags)

    elif mode_enum is Mode.BENCHMARK:
        if benchmark_runs is None:
            benchmark_runs = 100
        process_files_benchmark(files, tags, benchmark_runs)

    elif mode_enum is Mode.VERBOSE:
        process_files(files, tags, True)


def process_files(paths: Sequence[str],
                  tags: Sequence[str], verbose: bool):
    open_hook = io.open
    _line_prog = nline.get_newlines

    def line_prog(fin: IO) -> Sequence[str]:
        return _line_prog(fin, tags)

    writelines = _write_newlines_to_file
    res_tuples = [tup for tup in
                  (writelines(f, line_prog, open_hook) for f in paths)]
    if not verbose:
        for fin, _ in res_tuples:
            fin.close()

    else:
        for i, t in enumerate(res_tuples):
            fin, newlines = t
            _print_rawlines_pretty(paths[i], newlines)
            fin.close()


def process_files_printonly(paths: Sequence[str], tags: Sequence[str]):
    open_hook = open
    _line_prog = nline.get_newlines

    def line_prog(fin: IO) -> Sequence[str]:
        return _line_prog(fin, tags)

    readlines = _readlines_from_file
    res_tuples = [
        tup for tup in
        (readlines(f, line_prog, open_hook) for f in paths)
    ]

    for i, t in enumerate(res_tuples):
        fin, newlines = t
        _print_rawlines_pretty(paths[i], newlines)
        fin.close()


def process_files_benchmark(paths: Sequence[str],
                            tags: Sequence[str],
                            runs: int):

    def countline(path: str):
        with open(path) as fin:
            return len(list(fin))

    lines = 0
    for p in paths:
        lines += countline(p)
    total_lines = lines * runs

    open_time_data = []
    gen_newlines_time_data = []
    write_time_data = []
    close_time_data = []
    num_files = len(paths)
    num_runs = range(runs)

    for _ in num_runs:
        open_time, gen_newlines_time, write_time, close_time = \
            _time_process_files(paths, tags)
        open_time_data.append(open_time)
        gen_newlines_time_data.append(gen_newlines_time)
        write_time_data.append(write_time)
        close_time_data.append(close_time)

    total_runs = runs * num_files
    open_time_total = sum(open_time_data)
    gen_newlines_time_total = sum(gen_newlines_time_data)
    write_time_total = sum(write_time_data)
    close_time_total = sum(close_time_data)

    open_result = {
        "open_time_total": open_time_total,
        "open_time_avg_total": statistics.mean(open_time_data),
        "open_time_median_total": statistics.median(open_time_data),
        "open_time_avg_file": open_time_total / total_runs,
        "open_time_avg_line": open_time_total / total_lines,
    }

    newlines_result = {
        "gen_newlines_time_total": gen_newlines_time_total,
        "gen_newlines_time_avg_total": statistics.mean(gen_newlines_time_data),
        "gen_newlines_time_median_total": statistics.median(gen_newlines_time_data),
        "gen_newlines_avg_file": gen_newlines_time_total / total_runs,
        "gen_newlines_avg_line": gen_newlines_time_total / total_lines,
    }

    write_result = {
        "write_time_total": write_time_total,
        "write_time_avg_total": statistics.mean(write_time_data),
        "write_time_median_total": statistics.median(write_time_data),
        "write_time_avg_file": write_time_total / total_runs,
        "write_time_avg_line": write_time_total / total_lines,
    }

    close_result = {
        "close_time_total": close_time_total,
        "close_time_avg_total": statistics.mean(close_time_data),
        "close_time_median_total": statistics.median(close_time_data),
        "close_time_avg_file": close_time_total / total_runs,
        "close_time_avg_line": close_time_total / total_lines
    }

    time_taken_total = open_time_total + gen_newlines_time_total + \
        write_time_total + close_time_total

    time_taken_avg_line = open_result["open_time_avg_line"] + \
        newlines_result["gen_newlines_avg_line"] + \
        write_result["write_time_avg_line"] + \
        close_result["close_time_avg_line"]

    time_taken_avg_file = open_result["open_time_avg_file"] + \
        newlines_result["gen_newlines_avg_file"] + \
        write_result["write_time_avg_file"] + \
        close_result["close_time_avg_file"]

    summary = {
        "time_taken_total": time_taken_total,
        "time_taken_avg_file": time_taken_avg_file,
        "time_taken_avg_lines": time_taken_avg_line,
    }

    misc = {
        "Number of files": num_files,
        "Number of runs": runs,
        "Number of lines": lines,
        "Total number of lines": total_lines
    }

    _utils.pretty_print_title("PERFORMANCE REPORT", span=True)
    width = get_terminal_size().columns // 4
    print('')
    for k, v in misc.items():
        print(f"{k:{width}} {v:>{width}}")

    print('')

    _utils.pretty_print_title("Open file", span=True)
    print('')
    for k, v in open_result.items():
        print(f"{k:{width}} {v*1000:>{width - 2}.4f}ms")
    print('')

    _utils.pretty_print_title("Generate new lines", span=True)
    for k, v in newlines_result.items():
        print(f"{k:{width}} {v*1000:>{width - 2}.4f}ms")
    print('')

    _utils.pretty_print_title("Write new lines", span=True)
    for k, v in write_result.items():
        print(f"{k:{width}} {v*1000:>{width - 2}.4f}ms")
    print('')

    _utils.pretty_print_title("Close file", span=True)
    for k, v in close_result.items():
        print(f"{k:{width}} {v*1000:>{width - 2}.4f}ms")
    print('')

    _utils.pretty_print_title("Summary", span=True)
    for k, v in summary.items():
        print(f"{k:{width}} {v*1000:>{width - 2}.4f}ms")
    print('')

    _utils.pretty_print_title("END REPORT", span=True)


def _time_process_files(paths: Sequence[str],
                        tags: Sequence[str]) -> Tuple[float, ...]:

    def _open(path: IOType,
              timer: Callable[..., float],
              mode: str,
              open_hook: Callable[..., IO]) -> IO:
        return open_hook(path, mode)

    open_with_timer = _utils.time_fn(_open)

    def _newlines(fin: IO,
                  line_prog: LineProg,
                  timer: Callable[..., float]) -> Sequence[str]:
        return line_prog(fin, tags)

    newlines_with_timer = _utils.time_fn(_newlines)

    def _writelines(fin: IO,
                    newlines: Sequence[str],
                    timer: Callable[..., float]):
        fin.seek(0)
        fin.truncate()
        fin.writelines(newlines)

    write_newlines_with_timer = _utils.time_fn_only(_writelines)

    def _close(fin: IO, timer: Callable[..., float]):
        fin.close()

    close_with_timer = _utils.time_fn_only(_close)

    open_time_elapsed = 0
    gen_newlines_time_elapsed = 0
    write_time_elapsed = 0
    close_time_elapsed = 0
    tmp_files = []

    _open_hook = open
    _line_prog = nline.get_newlines
    _timer = time.monotonic
    mk_tmpfile = tempfile.TemporaryFile
    for p in paths:
        # copy src file to temp file, also time the opening process
        fin, open_time = open_with_timer(
            p, timer=_timer, mode='r', open_hook=_open_hook)
        open_time_elapsed += open_time
        src = fin.read()

        # close the src file here
        fin.close()

        # copy src to tmp
        tmp_file = mk_tmpfile(mode='w+')
        tmp_file.write(src)
        tmp_file.seek(0)

        # get & time newlines
        newlines, gen_newlines_time = newlines_with_timer(
            tmp_file, _line_prog, _timer)
        gen_newlines_time_elapsed += gen_newlines_time

        # time writing
        write_time_elapsed += write_newlines_with_timer(tmp_file, newlines, _timer)

        tmp_files.append(tmp_file)

    for f in tmp_files:
        close_time_elapsed += close_with_timer(f, _timer)

    return (
        open_time_elapsed, gen_newlines_time_elapsed,
        write_time_elapsed, close_time_elapsed)


def _write_newlines_to_file(
        path: IOType,
        line_prog: LineProg,
        open_hook: Callable[..., IO]) -> Tuple[IO, LineProgResult]:

    fi = open_hook(path, mode='r+')
    newlines = line_prog(fi)
    fi.seek(0)
    fi.truncate()
    fi.writelines(newlines)

    return fi, newlines


def _readlines_from_file(path: IOType,
                         line_prog: LineProg,
                         open_hook: Callable[..., IO]) -> Tuple[IO, LineProgResult]:
    fi = open_hook(path, mode='r')
    newlines = line_prog(fi)
    return fi, newlines


def _print_rawlines_pretty(fname: str, lines: Sequence[str]):
    _utils.pretty_print_title(fname, span=True)
    _utils.print_raw_lines(lines)
    _utils.pretty_print_title("EOF", span=True)
    print('')
