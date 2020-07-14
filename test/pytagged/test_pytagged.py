from pathlib import PurePath

import pytest

from pytagged import pytagged


TEST_FILES_PATH = "./test_files"


@pytest.mark.parametrize(
    "tags",
    [(",debug"),
     ("skip, ,debug"),
     ("slow, ,debug,,benchmark")]
)
def test_pytagged_get_newlines_raise_err(tags):
    tags = tags.split(',')
    path = PurePath(TEST_FILES_PATH, "hello.py")

    # call get_newlines with proper file arg, but with illegal tags
    # should raise ValueError
    with open(path) as f:
        with pytest.raises(ValueError):
            _ = pytagged.get_newlines(f, *tags)


@pytest.mark.parametrize(
    "target_file, tags",
    [("expected_hello.py", "debug"),
     ("expected_hello_skip.py", "skip"),
     ("expected_hello_slow.py", "slow")]
)
def test_pytagged_get_newlines(target_file, tags):
    target_path = PurePath(TEST_FILES_PATH, target_file)
    with open(target_path) as f:
        expected_lines = f.readlines()

    tags = tags.split(',')

    src_path = PurePath(TEST_FILES_PATH, "hello.py")
    with open(src_path) as f:
        src_lines = f.readlines()
        f.seek(0)
        actual_lines = pytagged.get_newlines(f, *tags)

    assert src_lines != expected_lines
    assert actual_lines == expected_lines
