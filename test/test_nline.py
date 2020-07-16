import pytest

from pytagged import nline, _utils
from conftest import path_to_src_file_singles


@pytest.mark.parametrize(
    "tags",
    [(",debug"),
     ("skip, ,debug"),
     ("slow, ,debug,,benchmark")]
)
def test_pytagged_get_newlines_raise_err(tags: str):
    tags = tags.split(',')
    path = path_to_src_file_singles("hello.py")

    # call get_newlines with proper file arg, but with illegal tags
    # should raise ValueError
    with open(path) as f:
        with pytest.raises(ValueError):
            nline.get_newlines(f, *tags)


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
    _utils.pretty_print_title("ACTUAL")
    _utils.print_raw_lines(actual_lines)
    print('\n')

    _utils.pretty_print_title("EXPECTED")
    _utils.print_raw_lines(expected_lines)

    assert src_lines != expected_lines
    assert actual_lines == expected_lines
