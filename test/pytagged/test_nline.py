from pathlib import PurePath

import pytest

from pytagged import nline, utils


@pytest.mark.parametrize(
    "tags",
    [(",debug"),
     ("skip, ,debug"),
     ("slow, ,debug,,benchmark")]
)
def test_pytagged_get_newlines_raise_err(test_files_path_singles, tags: str):
    tags = tags.split(',')
    path = PurePath(test_files_path_singles, "hello.py")

    # call get_newlines with proper file arg, but with illegal tags
    # should raise ValueError
    with open(path) as f:
        with pytest.raises(ValueError):
            _ = nline.get_newlines(f, *tags)


def test_pytagged_get_newlines(src_to_target_params):
    src_file, target_file = src_to_target_params[:2]
    tags = src_to_target_params[2:]
    print(tags)
    with open(target_file) as f:
        expected_lines = f.readlines()

    with open(src_file) as f:
        src_lines = f.readlines()
        f.seek(0)
        actual_lines = nline.get_newlines(f, *tags)
    utils.pretty_print_title("ACTUAL")
    utils.print_raw_lines(actual_lines)
    print('\n')

    utils.pretty_print_title("EXPECTED")
    utils.print_raw_lines(expected_lines)

    assert src_lines != expected_lines
    assert actual_lines == expected_lines
