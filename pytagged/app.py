import argparse
import configparser
import io
import os
import statistics
import sys
import tempfile
import textwrap
import time
from shutil import get_terminal_size
from typing import (
    Callable, IO,
    Sequence, Optional,
    Iterable, Iterator, Tuple, Union,
)

# only import resource if linux
if sys.platform.startswith("linux"):
    import resource

from pytagged._mode import Mode
from pytagged import _files_utils
from pytagged import _utils
from pytagged import nline
from pytagged.options import Options


# types
LineProg = Callable[[IO, Iterable[str]], Sequence[str]]
LineProgResult = Optional[Sequence[str]]
IOType = Union[IO, str]

# version control, cache, eggs & envs
# some of these are taken from the default
# that flake8 uses
DEFAULT_EXCLUDED_PATTERNS = [
    ".svn", "CVS", ".bzr", ".hg", ".git",
    "__pycache__", ".tox", ".eggs", "*.egg",
]
PY_EXT = '.py'


class NoOptionsException(Exception):
    pass


class App:
    def __init__(self):
        # fallback
        self.default_path = '.'
        self.default_excluded = DEFAULT_EXCLUDED_PATTERNS
        self.default_config_file = "pytagged.ini"
        self.extension = PY_EXT
        self.mode = Mode.DEFAULT
        self.verbosity = 0
        self.benchmark_runs = 100

    def run(self):
        try:
            options = self.get_opts()
        except NoOptionsException:
            sys.stderr.write(
                "Error: no configs and no cli arguments\n")
            sys.exit(1)

        # block: develop
        _utils.pretty_print_title("Options", span=True)
        print(f"path: {options.path}")
        print(f"tags: {options.tags}")
        print(f"config_path: {options.config_path}")
        print(f"excluded patterns: {options.exclude}")
        print(f"extend excluded: {options.extend_exclude}")
        print(f"mode: {options.mode.name}")
        print(f"benchmark runs: {options.benchmark_runs}")
        print(f"verbosity: {options.verbosity}")
        print('')
        # end

        # need tags
        if not options.tags:
            sys.stderr.write(
                "Error: no tags provided through cli or config file"
            )
            sys.exit(1)

        path = options.path
        if not path:
            path = self.default_path

        tags = set()

        for i, t in enumerate(options.tags):
            stripped = t.strip()
            if not stripped:
                sys.stderr.write(
                    "Error: tag cannot be an empty string or only whitespaces\n")
                sys.exit(1)
            tags.add(stripped)

        excluded_patterns = options.exclude
        if excluded_patterns is None:
            excluded_patterns = self.default_excluded

        if options.extend_exclude is not None:
            excluded_patterns += options.extend_exclude
        excluded_patterns = [i.strip() for i in excluded_patterns]
        excluded_patterns = [i for i in excluded_patterns if i]

        def exclude(pth: str) -> bool:
            return _files_utils.match_path(pth, excluded_patterns)

        gen_files = _files_utils.filepaths_from_path(path, is_excluded=exclude)
        files = [f for f in gen_files if f.endswith(self.extension)]

        if not files:
            print(f"Found no files matching pattern: {path}")
            sys.exit(0)

        self.mode = options.mode
        if options.verbosity is not None:
            self.verbosity = options.verbosity

        benchmark_runs = options.benchmark_runs
        if benchmark_runs is not None:
            if benchmark_runs not in (0, -1):
                if benchmark_runs < -1:
                    sys.stderr.write("Benchmark runs must be positive\n")
                    sys.exit(1)
                self.benchmark_runs = benchmark_runs

        num_files = len(files)
        # block: develop
        _utils.pretty_print_title("Run info", span=True)
        print(f"Mode: {self.mode.name.lower()}")
        print(f"On path: {path}")
        print(f"Using tags: {', '.join(tags)}")
        print(f"Excluding: {excluded_patterns}")
        print(f"Verbosity: {self.verbosity}")
        print(f"Number of files: {num_files}")
        print('')

        # end
        if self.verbosity > 0:
            _utils.pretty_print_title("More Info", span=True)
            print(f"Collected {num_files} files:")
            if num_files < 10:
                for f in files:
                    print(f)

        # TODO: handle file resources for windows/mac
        if "resource" in sys.modules:
            soft_lim, hard_lim = resource.getrlimit(resource.RLIMIT_NOFILE)
            print("Hard limit of file descriptors: ", hard_lim)     # develop

            if soft_lim < num_files:
                if not self._try_request_resource(resource.RLIMIT_NOFILE,
                                                  (num_files, hard_lim)):
                    sys.stderr("Cannot acquire file resources, exiting")
                    sys.exit(1)

        try:

            self._run(files, tags)
            sys.exit(0)
        except OSError as e:
            sys.stderr.write(str(e))
            sys.exit(1)
        except KeyboardInterrupt:
            sys.stderr.write("Interrupted while still working")
            sys.exit(1)

    def get_opts(self) -> Options:
        """Get options, first from cli args,
        if there are none, look for the default
        config file.

        If the cli args provide a path to a config file,
        the options from that config file will take precedence
        over the cli args.
        """
        options = self._get_cli_opts()

        if options is None:     # no cli args, fallback to configs
            options = self._get_cfg_opts(self.default_config_file)
            if options is None:
                raise NoOptionsException
            return options

        if options.config_path:     # get cfg options if provided
            cfg_options = self._get_cfg_opts(options.config_path)
            options = cfg_options.replace_if_not_none(options)
        return options

    def create_config_file_from_options(self,
                                        options: Options,
                                        config_path: str = None) -> str:

        _options = options._asdict()
        if config_path is None:
            try:
                config_path = _options.pop("config_path")
            except KeyError:
                config_path = None
        if config_path is None:
            raise ValueError("no config path provided")

        cfg_options = {}

        cfg_options = {k: v for k, v in _options.items() if v is not None}
        for k in cfg_options:
            v = cfg_options[k]
            if isinstance(v, list):
                cfg_options[k] = ','.join(i.strip() for i in v)

        mode = cfg_options["mode"]
        cfg_options["mode"] = mode.name.lower()

        config = configparser.ConfigParser()
        config["pytagged"] = cfg_options
        with open(config_path, 'w') as f:
            config.write(f)
        return config_path

    def default_opts(self) -> Options:
        return Options(
            path=self.default_path,
            config_path=self.default_config_file,
            tags=["debug"],
            exclude=self.default_excluded,
            extend_exclude=[],
            mode=Mode.DEFAULT,
            verbosity=0,
            benchmark_runs=self.benchmark_runs)

    def _try_request_resource(self,
                              rsrc: int,
                              new_lim: Tuple[int, int]) -> bool:
        try:
            resource.setrlimit(rsrc, limits=new_lim)
            return True
        except (OSError, ValueError):
            return False

    def _run(self, paths: str, tags: str):
        if self.mode is Mode.DEFAULT:
            self._proc_files(paths, tags)

        elif self.mode is Mode.PRINTONLY:
            self._proc_files_printonly(paths, tags)

        elif self.mode is Mode.BENCHMARK:
            self._proc_files_benchmark(paths, tags)

    def _get_cli_opts(self) -> Optional[Options]:
        arg_parser = argparse.ArgumentParser(
            description="Comment out tagged code in your python code",
            add_help=False,
            formatter_class=argparse.RawTextHelpFormatter)

        # required args
        arg_parser.add_argument("path",
                                type=str,
                                nargs='?',
                                default='',
                                help=textwrap.dedent("""\
                                    path to python file(s),
                                    if this is a directory, the program
                                    will work on all files with the .py
                                    extention within that directory.
                                    Defaults to the current working dir.\n"""))

        arg_parser.add_argument("-cf", "--config",
                                type=str,
                                default='',
                                help=textwrap.dedent("""\
                                    path to a .cfg format file containing
                                    the configurations options to run
                                    pytagged. Note that if this is provided,
                                    the options found in the file will
                                    override the options provided through
                                    the cli.\n \n"""))

        arg_parser.add_argument("-t", "--tags",
                                type=str,
                                nargs='*',
                                help=textwrap.dedent("""\
                                one or more 'tags', this tells
                                the program what to comment out.\n \n"""))

        arg_parser.add_argument("-x", "--exclude",
                                type=str,
                                nargs='*',
                                help=textwrap.dedent("""\
                                    exclude paths that match against
                                    these patterns, this will override
                                    the default patterns.\n \n"""))

        arg_parser.add_argument("-xt", "--extend-exclude",
                                dest="extend_exclude",
                                type=str,
                                nargs='*',
                                help=textwrap.dedent("""\
                                    exclude paths that match against
                                    these patterns, this will be used
                                    along with the default patterns.\n \n"""))

        arg_parser.add_argument("-v", "--verbosity",
                                type=int,
                                choices=[0, 1],
                                default=None,
                                help=textwrap.dedent("""\
                                verbosity, select the verbosity of the output.
                                Defaults to 0, no output."""))

        # optional args
        arg_parser.add_argument("-h", "--help",
                                action="store_true",
                                help="Show help message & exit.\n \n")

        modes = arg_parser.add_mutually_exclusive_group()
        modes.add_argument("-b", "--benchmark",
                           type=int,
                           nargs='?',
                           default=0,
                           const=-1,
                           help=textwrap.dedent("""\
                                Number of benchmark runs, if this is supplied
                                the program will run for N times, and print out
                                some performance statistics. Note that after PyTagged
                                is done, files will be restored to their original
                                content. Will also ignore the -v flag.\n \n"""))

        modes.add_argument("-p", "--printonly",
                           action="store_true",
                           help=textwrap.dedent("""\
                                Print only mode, if this flag is equivalent
                                to the -v flag but the program will not modify
                                file(s).\n \n"""))

        args = arg_parser.parse_args()

        try:
            _ = sys.argv[1]
        except IndexError:
            return None

        if args.help:
            arg_parser.print_help()
            sys.exit(0)

        mode_int = 0
        if args.printonly:
            mode_int = 1
        elif args.benchmark:
            mode_int = 2

        return Options(
            path=args.path,
            config_path=args.config,
            tags=args.tags,
            exclude=args.exclude,
            extend_exclude=args.extend_exclude,
            mode=Mode(mode_int),
            benchmark_runs=args.benchmark,
            verbosity=args.verbosity
        )

    def _get_cfg_opts(self, path: str) -> Optional[Options]:
        path = os.path.abspath(path)
        if os.path.exists(path):
            config = configparser.ConfigParser()
            try:
                config.read(path)
            except IOError:
                return None

            try:
                section = config["pytagged"]
            except KeyError:
                return None

            fields = Options._fields
            opt_dict = {k: section[k] for k in section if k in fields}

            def split_and_strip(s: str) -> Iterator[str]:
                yield from (c.strip() for c in s.split(','))

            if "tags" in opt_dict:
                tags_str = opt_dict["tags"]
                opt_dict["tags"] = [i for i in split_and_strip(tags_str) if i]

            if "exclude" in opt_dict:
                exclude_str = opt_dict["exclude"]
                opt_dict["exclude"] = [i for i in split_and_strip(exclude_str) if i]

            if "extend_exclude" in opt_dict:
                extend_str = opt_dict["extend_exclude"]
                opt_dict["extend_exclude"] = [
                    i for i in split_and_strip(extend_str) if i]

            if "mode" in opt_dict:
                mode = opt_dict["mode"]
                try:
                    opt_dict["mode"] = Mode[mode.upper()]
                except KeyError:
                    opt_dict = Mode.DEFAULT

            if "benchmark_runs" in opt_dict:
                if "mode" not in opt_dict:
                    opt_dict["mode"] = Mode.BENCHMARK
                benchmark_runs = opt_dict["benchmark_runs"]
                try:
                    opt_dict["benchmark_runs"] = int(benchmark_runs)
                except ValueError:
                    opt_dict["benchmark_runs"] = None
            if "verbosity" in opt_dict:
                verbosity = opt_dict["verbosity"]
                try:
                    opt_dict["verbosity"] = int(verbosity)
                except ValueError:
                    opt_dict["verbosity"] = None

            return Options(**opt_dict)

        return None

    def _proc_files(self, paths: Sequence[str], tags: Sequence[str]):
        open_hook = io.open
        _line_prog = nline.get_newlines

        def line_prog(fin: IO) -> Sequence[str]:
            return _line_prog(fin, tags)

        res_tuples = [tup for tup in
                      (self._write_newlines_to_file(f, line_prog, open_hook)
                       for f in paths)]
        if self.verbosity < 1:
            for fin, _ in res_tuples:
                fin.close()

        else:
            for i, t in enumerate(res_tuples):
                fin, newlines = t
                self._print_rawlines_pretty(paths[i], newlines)
                fin.close()

    def _proc_files_printonly(self, paths: Sequence[str], tags: Sequence[str]):
        open_hook = open
        _line_prog = nline.get_newlines

        def line_prog(fin: IO) -> Sequence[str]:
            return _line_prog(fin, tags)

        res_tuples = [
            tup for tup in
            (self._readlines_from_file(f, line_prog, open_hook) for f in paths)
        ]

        for i, t in enumerate(res_tuples):
            fin, newlines = t
            self._print_rawlines_pretty(paths[i], newlines)
            fin.close()

    def _proc_files_benchmark(self, paths: Sequence[str], tags: Sequence[str]):

        def countline(path: str):
            with open(path) as fin:
                return len(list(fin))
        lines = 0
        runs = self.benchmark_runs
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
                self._time_process_files(paths, tags)
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
            "gen_newlines_time_total":
            gen_newlines_time_total,
            "gen_newlines_time_avg_total":
            statistics.mean(gen_newlines_time_data),
            "gen_newlines_time_median_total":
            statistics.median(gen_newlines_time_data),
            "gen_newlines_avg_file":
            gen_newlines_time_total / total_runs,
            "gen_newlines_avg_line":
            gen_newlines_time_total / total_lines,
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

    def _time_process_files(self, paths: Sequence[str],
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
            write_time_elapsed += write_newlines_with_timer(
                tmp_file, newlines, _timer)

            tmp_files.append(tmp_file)

        for f in tmp_files:
            close_time_elapsed += close_with_timer(f, _timer)

        return (
            open_time_elapsed, gen_newlines_time_elapsed,
            write_time_elapsed, close_time_elapsed)

    def _write_newlines_to_file(
            self,
            path: IOType,
            line_prog: LineProg,
            open_hook: Callable[..., IO]) -> Tuple[IO, LineProgResult]:

        fi = open_hook(path, mode='r+')
        newlines = line_prog(fi)
        fi.seek(0)
        fi.truncate()
        fi.writelines(newlines)

        return fi, newlines

    def _readlines_from_file(
            self,
            path: IOType,
            line_prog: LineProg,
            open_hook: Callable[..., IO]) -> Tuple[IO, LineProgResult]:
        fi = open_hook(path, mode='r')
        newlines = line_prog(fi)
        return fi, newlines

    def _print_rawlines_pretty(self, fname: str, lines: Sequence[str]):
        _utils.pretty_print_title(fname, span=True)
        _utils.print_raw_lines(lines)
        _utils.pretty_print_title("EOF", span=True)
        print('')
