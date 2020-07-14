from pathlib import PurePath
from typing import List
from os import get_terminal_size

import pytest

from pytagged import pytagged, utils


TEST_FILES_PATH = "./test_files"


@pytest.mark.parametrize(
    "tags",
    [(",debug"),
     ("skip, ,debug"),
     ("slow, ,debug,,benchmark")]
)
def test_pytagged_get_newlines_raise_err(tags: str):
    tags = tags.split(',')
    path = PurePath(TEST_FILES_PATH, "hello.py")

    # call get_newlines with proper file arg, but with illegal tags
    # should raise ValueError
    with open(path) as f:
        with pytest.raises(ValueError):
            _ = pytagged.get_newlines(f, *tags)


@pytest.mark.parametrize(
    "src_file, target_file, tags",
    [("hello.py", "expected_hello.py", "debug"),
     ("hello.py", "expected_hello_skip.py", "skip"),
     ("hello.py", "expected_hello_slow.py", "slow"),
     ("hello_no_block.py", "expected_hello_no_block.py", "debug,skip,slow"),
     ("triple_quote.py", "expected_triple_quote.py", "debug")]
)
def test_pytagged_get_newlines(src_file: str, target_file: str, tags: str):
    target_path = PurePath(TEST_FILES_PATH, target_file)
    with open(target_path) as f:
        expected_lines = f.readlines()

    tags = tags.split(',')

    src_path = PurePath(TEST_FILES_PATH, src_file)
    with open(src_path) as f:
        src_lines = f.readlines()
        f.seek(0)
        actual_lines = pytagged.get_newlines(f, *tags)
    utils.pretty_print_title("ACTUAL")
    utils.print_raw_lines(actual_lines)
    print('\n')

    utils.pretty_print_title("EXPECTED")
    utils.print_raw_lines(actual_lines)

    assert src_lines != expected_lines
    assert actual_lines == expected_lines
