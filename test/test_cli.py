from pathlib import Path
import subprocess

import pytest

from conftest import path_to_multiples
from pytagged._utils import print_raw_lines, pretty_print_title
from pytagged._files_utils import filepaths_from_path


TAG_FLAGS = ["-t", "--tags"]
VERBOSE_FLAGS = ["-v", "--verbose"]
PRINTONLY_FLAGS = ["-p", "--printonly"]
BENCHMARK_FLAGS = ["-b", "--benchmark"]


@pytest.fixture(params=TAG_FLAGS)
def flag_tag(request):
    return request.param


@pytest.fixture(params=VERBOSE_FLAGS)
def flag_verbose(request):
    return request.param


@pytest.fixture(params=PRINTONLY_FLAGS)
def flag_printonly(request):
    return request.param


@pytest.fixture(params=BENCHMARK_FLAGS)
def flag_benchmark(request):
    return request.param


@pytest.mark.parametrize(
    "tags",
    [
        ["debug", "", "other_tag"],
        ["", "debug", "other_tag"],
        ["debug", "other_tag", ""],
        [" ", "debug", "other_tag", "", "   "]
    ]
)
def test_cli_empty_tags(tags, flag_tag):
    path = path_to_multiples()
    files = filepaths_from_path(path, is_excluded=lambda x: False)

    # Read in the file contents
    src_content = []
    for f in files:
        with open(f) as fin:
            src_content.append(fin.read())

    cmd = ["pytag", path, flag_tag, *tags]
    completed = subprocess.run(cmd)
    assert completed.returncode == 1

    # Check that nothing was changed
    for i, f in enumerate(files):
        with open(f) as fin:
            assert src_content[i] == fin.read()


def test_cli_singles(cleanup_test_path_singles, src_to_target_params, flag_tag):
    src_path = src_to_target_params[0]
    target_path = src_to_target_params[1]
    tags = src_to_target_params[2:]

    cmd = ["pytag", src_path, flag_tag, *tags]
    print(cmd)
    subprocess.run(cmd, check=True)

    with open(src_path) as f:
        src_lines = f.readlines()

    with open(target_path) as f:
        target_lines = f.readlines()

    pretty_print_title(src_path)
    print_raw_lines(src_lines)
    print('')
    pretty_print_title(target_path)
    print_raw_lines(target_lines)
    print('')

    assert src_lines == target_lines


def test_cli_singles_verbose(cleanup_test_path_singles,
                             src_to_target_params,
                             flag_tag,
                             flag_verbose):
    src_path = src_to_target_params[0]
    target_path = src_to_target_params[1]
    tags = src_to_target_params[2:]

    cmd = ["pytag", src_path, flag_tag, *tags, flag_verbose]
    print(cmd)
    subprocess.run(cmd, check=True)

    with open(src_path) as f:
        src_lines = f.readlines()

    with open(target_path) as f:
        target_lines = f.readlines()

    pretty_print_title(src_path)
    print_raw_lines(src_lines)
    print('')
    pretty_print_title(target_path)
    print_raw_lines(target_lines)
    print('')

    assert src_lines == target_lines


def test_cli_multiples(cleanup_test_path_multiples,
                       src_to_target_params_multiples,
                       flag_tag):

    src_path, target_path = src_to_target_params_multiples[:2]
    tags = src_to_target_params_multiples[2:]
    cmd = ["pytag", src_path, flag_tag, *tags]

    print(cmd)
    subprocess.run(cmd, check=True)

    expected_contents = {}
    for f in Path(target_path).glob(r"**/*.py"):
        fname = f.parts[-1]
        with f.open() as fin:
            expected_contents[fname] = fin.readlines()

    actual_contents = {}
    for f in Path(src_path).glob(r"**/*.py"):
        fname = f.parts[-1]
        with f.open() as fin:
            actual_contents[fname] = fin.readlines()

    for name in actual_contents:
        actual = actual_contents[name]
        expected = expected_contents[f"expected_{name}"]
        assert actual == expected


def test_cli_multiples_verbose(cleanup_test_path_multiples,
                               src_to_target_params_multiples,
                               flag_verbose):

    src_path, target_path = src_to_target_params_multiples[:2]
    tags = src_to_target_params_multiples[2:]
    cmd = ["pytag", src_path, "-t", *tags, flag_verbose]

    print(cmd)
    subprocess.run(cmd, check=True)

    expected_contents = {}
    for f in Path(target_path).glob(r"**/*.py"):
        fname = f.parts[-1]
        with f.open() as fin:
            expected_contents[fname] = fin.readlines()

    actual_contents = {}
    for f in Path(src_path).glob(r"**/*.py"):
        fname = f.parts[-1]
        with f.open() as fin:
            actual_contents[fname] = fin.readlines()

    for name in actual_contents:
        actual = actual_contents[name]
        expected = expected_contents[f"expected_{name}"]
        assert actual == expected


@pytest.mark.parametrize(
    "tags",
    [
        ["debug", "tag", "other_tag"],
        ["some_tag", "debug", "other_tag"],
        ["debug", "other_tag", "some_dumb_tag"],
        ["fan_tag_stick", "debug", "other_tag", "bro_tag", "suhhhhh"]
    ]
)
def test_cli_printonly(tags, flag_printonly):
    path = path_to_multiples()
    files = filepaths_from_path(path, is_excluded=lambda x: False)

    # Read in the file contents
    src_content = []
    for f in files:
        with open(f) as fin:
            src_content.append(fin.read())

    cmd = ["pytag", path, "-t", *tags, flag_printonly]
    subprocess.run(cmd, check=True)

    # Check that nothing was changed
    for i, f in enumerate(files):
        with open(f) as fin:
            assert src_content[i] == fin.read()
