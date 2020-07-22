import configparser
import os
from pathlib import Path
import subprocess
from typing import (
    Sequence, Mapping,
    Iterator, Tuple
)

import pytest

from conftest import (
    path_to_multiples,
    read_python_files_as_dict,
    write_file_from_dict,
    TEST_FILES_PATH
)
from pytagged._utils import print_raw_lines, pretty_print_title
from pytagged._files_utils import filepaths_from_path
from pytagged._mode import Mode


TAG_FLAGS = ["-t", "--tags"]
VERBOSE_FLAGS = ["-v", "--verbosity"]
PRINTONLY_FLAGS = ["-p", "--printonly"]
BENCHMARK_FLAGS = ["-b", "--benchmark"]
CONFIG_FLAGS = ["-cf", "--config"]
EXCLUDE_FLAGS = ["-x", "--exclude"]
EXTEND_FLAGS = ["-xt", "--extend-exclude"]


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


@pytest.fixture(params=CONFIG_FLAGS)
def flag_config(request):
    return request.param


@pytest.fixture(params=EXCLUDE_FLAGS)
def flag_exclude(request):
    return request.param


@pytest.fixture(params=EXTEND_FLAGS)
def flag_extend(request):
    return request.param


@pytest.fixture
def generate_options_exclude(
        src_to_target_params_multiples) -> Iterator[Tuple[str, ...]]:
    src_path, target_path = src_to_target_params_multiples[:2]
    working_path = os.path.commonpath([src_path, target_path])
    exclude = os.path.basename(target_path)
    tags = src_to_target_params_multiples[2:]

    config_path = f"{TEST_FILES_PATH}/configs.ini"
    config = configparser.ConfigParser()

    section = {
        "path": working_path,
        "config_path": config_path,
        "tags": ','.join(tags),
        "exclude": exclude
    }
    config["pytagged"] = section

    with open(config_path, 'w') as f:
        config.write(f)

    yield (config_path, *src_to_target_params_multiples)
    os.remove(config_path)


def read_config(config_path: str) -> Mapping[str, str]:
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def print_rawlines_pretty(name: str, lines: Sequence[str]):
    pretty_print_title(name)
    print_raw_lines(lines)
    print('')


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

    print_rawlines_pretty(src_path, src_lines)
    print_rawlines_pretty(target_path, target_lines)

    assert src_lines == target_lines


def test_cli_singles_verbose(cleanup_test_path_singles,
                             src_to_target_params,
                             flag_tag,
                             flag_verbose):
    src_path = src_to_target_params[0]
    target_path = src_to_target_params[1]
    tags = src_to_target_params[2:]

    cmd = ["pytag", src_path, flag_tag, *tags, flag_verbose, "1"]
    print(cmd)
    subprocess.run(cmd, check=True)

    with open(src_path) as f:
        src_lines = f.readlines()

    with open(target_path) as f:
        target_lines = f.readlines()

    print_rawlines_pretty(src_path, src_lines)
    print_rawlines_pretty(target_path, target_lines)

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
                               flag_tag,
                               flag_verbose):

    src_path, target_path = src_to_target_params_multiples[:2]
    tags = src_to_target_params_multiples[2:]
    cmd = ["pytag", src_path, flag_tag, *tags, flag_verbose, "1"]

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


def test_cli_singles_with_opt_from_cfg(cleanup_test_path_singles,
                                       src_to_target_params_singles_use_config,
                                       flag_config):
    config_path, target_path = src_to_target_params_singles_use_config

    cmd = ["pytag", flag_config, config_path]
    subprocess.run(cmd, check=True)

    config = read_config(config_path)
    src_path = config["pytagged"]["path"]
    with open(src_path) as f:
        src_lines = f.readlines()

    with open(target_path) as f:
        target_lines = f.readlines()

    print_rawlines_pretty(src_path, src_lines)
    print_rawlines_pretty(target_path, target_lines)
    assert src_lines == target_lines


def test_cli_multiples_with_opt_from_cfg(cleanup_test_path_multiples,
                                         src_to_target_params_multiples_use_config,
                                         flag_config):
    config_path, target_path = src_to_target_params_multiples_use_config

    cmd = ["pytag", flag_config, config_path]
    subprocess.run(cmd, check=True)
    config = read_config(config_path)
    src_path = config["pytagged"]["path"]

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


def test_cli_exclude(cleanup_test_path_multiples,
                     src_to_target_params_multiples,
                     flag_tag,
                     flag_exclude):
    src_path, target_path = src_to_target_params_multiples[:2]
    working_path = os.path.commonpath([src_path, target_path])
    exclude = os.path.basename(target_path)
    tags = src_to_target_params_multiples[2:]

    # run pytagged on the parent dir excuding the src path, should be equivalent
    # to running pytagged on the src path
    cmd = ["pytag", working_path, flag_exclude, exclude, flag_tag, *tags]
    subprocess.run(cmd, check=True)
    # same test as test_cli_multiples
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


def test_cli_exclude_use_cfg(cleanup_test_path_multiples,
                             generate_options_exclude,
                             flag_tag,
                             flag_exclude,
                             flag_config):
    """Test if running with exclude options from config file
    is equivalent to running with exclude options from cli
    """
    config_path = generate_options_exclude[0]
    src_path = generate_options_exclude[1]
    target_path = generate_options_exclude[2]
    tags = generate_options_exclude[3:]
    working_path = os.path.commonpath([src_path, target_path])
    exclude = os.path.basename(target_path)

    # read in original files first
    og_contents = read_python_files_as_dict(src_path)

    # run with exclude options from the command line first
    cmd = ["pytag", working_path, flag_exclude, exclude, flag_tag, *tags]
    subprocess.run(cmd, check=True)
    expected_contents = read_python_files_as_dict(src_path)

    # restore the files for a second run
    write_file_from_dict(og_contents)

    # run with exclude options from config file
    cmd = ["pytag", flag_config, config_path]
    subprocess.run(cmd, check=True)
    actual_contents = read_python_files_as_dict(src_path)

    for name in actual_contents:
        actual = actual_contents[name]
        expected = expected_contents[name]
        assert actual == expected


def test_cli_no_cli_args(generate_default_test_config,
                         flag_tag, flag_exclude, flag_extend,
                         flag_verbose, flag_printonly, flag_benchmark):
    """This test uses the config file generated.
    This is meant to test working with a config file works
    correctly with no cli args. Using options from the config
    file should be equivalent to using the same options from
    the cli.
    """
    config_path = generate_default_test_config
    print(config_path)
    config = read_config(config_path)
    pytagged_section = config["pytagged"]
    src_file_path = pytagged_section["path"]
    og_file_contents = read_python_files_as_dict(src_file_path)

    tags = [i.strip() for i in pytagged_section["tags"].split(',')]
    exclude = [i.strip() for i in pytagged_section["exclude"].split(',')]
    extend = [i.strip() for i in pytagged_section["extend_exclude"].split(',')]

    args = [
        src_file_path,
        flag_tag, *tags,
        flag_exclude, *exclude,
        flag_extend, *extend,
        flag_verbose, pytagged_section["verbosity"]
    ]
    mode = pytagged_section["mode"]
    if mode is Mode.PRINTONLY:
        args.append(flag_printonly)
    elif mode is Mode.BENCHMARK:
        args.append(flag_benchmark)
        args.append(config["benchmark_runs"])

    # use pytag with cli args first
    cmd = ["pytag", *args]
    subprocess.run(cmd, check=True)

    cli_result = read_python_files_as_dict(src_file_path)

    # restore the original content
    write_file_from_dict(og_file_contents)

    cmd = ["pytag"]
    subprocess.run(cmd, check=True)

    cfg_result = read_python_files_as_dict(src_file_path)

    for k in cli_result:
        cli_lines = cli_result[k]
        cfg_lines = cfg_result[k]
        assert cli_lines == cfg_lines

    # restore again
    write_file_from_dict(og_file_contents)


def test_cli_mixins(cleanup_test_path_singles,
                    generate_options_mixins,
                    flag_config,
                    flag_tag):
    """Runs pytagged with mixed options from both cli
    and cfg/ini file. The test expects the tags to be
    provided by the cli, and the path to be provided
    by the config file. Should be the same result as
    test_cli_singles
    """

    config_path = generate_options_mixins[0]
    src_path = generate_options_mixins[1]
    target_path = generate_options_mixins[2]
    tags = generate_options_mixins[3:]

    cmd = ["pytag", flag_config, config_path, flag_tag, *tags]
    subprocess.run(cmd, check=True)

    with open(src_path) as f:
        src_lines = f.readlines()

    with open(target_path) as f:
        target_lines = f.readlines()

    print_rawlines_pretty(src_path, src_lines)
    print_rawlines_pretty(target_path, target_lines)

    assert src_lines == target_lines


def test_cli_mixins_verbose(cleanup_test_path_singles,
                            generate_options_mixins,
                            flag_config,
                            flag_tag,
                            flag_verbose):
    # same as test_cli_mixins but with verbose flag
    config_path = generate_options_mixins[0]
    src_path = generate_options_mixins[1]
    target_path = generate_options_mixins[2]
    tags = generate_options_mixins[3:]

    cmd = ["pytag", flag_config, config_path, flag_tag, *tags]
    subprocess.run(cmd, check=True)

    with open(src_path) as f:
        src_lines = f.readlines()

    with open(target_path) as f:
        target_lines = f.readlines()

    print_rawlines_pretty(src_path, src_lines)
    print_rawlines_pretty(target_path, target_lines)

    assert src_lines == target_lines
