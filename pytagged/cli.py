import argparse
import sys
import textwrap

from pytagged import app


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

    arg_parser.add_argument("-x", "--exclude",
                            type=str,
                            nargs='*',
                            help=textwrap.dedent("""\
                            exclude paths that match against these patterns"""))

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

    mode = 0
    if args.printonly:
        mode = 1
    elif args.benchmark:
        mode = 2
    elif args.verbose:
        mode = 3

    app.run(mode, args.path, args.tags, args.benchmark, args.exclude)
