import configparser
from pathlib import Path
import os
from typing import Tuple, Iterator
from string import Template
from typing import Mapping, Dict, List

import pytest

from pytagged.app import App


TEST_FILES_PATH = "./test_files"
PARAMS = [("hello.py", "expected_hello.py", "debug"),
          ("hello.py", "expected_hello_skip.py", "skip"),
          ("hello.py", "expected_hello_slow.py", "slow"),
          ("hello_no_block.py", "expected_hello_no_block.py",
           "debug", "skip", "slow"),
          ("triple_quote.py", "expected_triple_quote.py", "debug"),
          ("triple_quote_single.py", "expected_triple_quote_single.py", "debug"),
          ("fake_block.py", "expected_fake_block.py", "debug"),]

PARAMS_MULTIPLES = [("src", "target", "debug")]


src_singles_path_template = Template(
    f"{TEST_FILES_PATH}/singles/src/$filename")
src_multiples_path_template = Template(
    f"{TEST_FILES_PATH}/multiples/src/$filename")
target_singles_path_template = Template(
    f"{TEST_FILES_PATH}/singles/target/$filename")
target_multiples_path_template = Template(
    f"{TEST_FILES_PATH}/multiples/target/$filename")


def path_to_src_file_singles(fname: str) -> str:
    return src_singles_path_template.substitute(filename=fname)


def path_to_src_file_multiples(fname: str) -> str:
    return src_multiples_path_template.substitute(filename=fname)


def path_to_target_file_singles(fname: str) -> str:
    return target_singles_path_template.substitute(filename=fname)


def path_to_target_file_multiples(fname: str) -> str:
    return target_multiples_path_template.substitute(filename=fname)


def path_to_multiples() -> str:
    return f"{TEST_FILES_PATH}/multiples"


def read_python_files_as_dict(path: str) -> Dict[str, List[str]]:
    file_contents = {}
    for f in Path(path).glob(r"**/*.py"):
        fname = str(f)
        with f.open() as fin:
            file_contents[fname] = fin.readlines()
    return file_contents


def write_file_from_dict(contents: Mapping[str, List[str]]):
    for filename, lines in contents.items():
        with open(filename, 'w') as f:
            f.writelines(lines)


@pytest.fixture()
def generate_default_test_config() -> Iterator[str]:
    """Generate a config file using the default
    options, replacing the path to the test files
    path
    """
    app = App()
    default_options = app.default_opts()
    # set the path to the multiple src
    test_src_file_path = f"{path_to_multiples()}/src"
    default_options = default_options._replace(path=test_src_file_path)
    config_path = app.create_config_file_from_options(default_options)

    yield config_path
    os.remove(config_path)


@pytest.fixture
def generate_options_mixins(src_to_target_params):
    """Mix between cli & and cfg opts. Cli provides
    tags, cfg provides path.
    """
    app = App()
    options = app.default_opts()
    src_path = src_to_target_params[0]
    options = options._replace(path=src_path, tags=[])
    print(options)
    config_path = app.create_config_file_from_options(options)

    # yield the config path and the parameters
    yield (config_path, *src_to_target_params)

    os.remove(config_path)


@pytest.fixture(params=PARAMS)
def src_to_target_params(request) -> Tuple[str, ...]:

    src_path = path_to_src_file_singles(request.param[0])
    target_path = path_to_target_file_singles(request.param[1])

    return (src_path, target_path, *request.param[2:])


@pytest.fixture(params=PARAMS)
def src_to_target_params_singles_use_config(request) -> Tuple[str, ...]:
    config = configparser.ConfigParser()
    src_path = path_to_src_file_singles(request.param[0])
    target_path = path_to_target_file_singles(request.param[1])

    config_path = f"{TEST_FILES_PATH}/test.ini"

    section = {
        "path": src_path,
        "config_path": config_path,
        "tags": ','.join(request.param[2:])
    }

    config["pytagged"] = section

    # write config
    with open(config_path, 'w') as f:
        config.write(f)

    yield config_path, target_path
    os.remove(config_path)


@pytest.fixture(scope="module", params=PARAMS_MULTIPLES)
def src_to_target_params_multiples(request) -> Tuple[str, ...]:
    src_dir_param = request.param[0]
    target_dir_param = request.param[1]
    tags = request.param[2:]
    parent_path = path_to_multiples()
    src_path = f"{parent_path}/{src_dir_param}"
    target_path = f"{parent_path}/{target_dir_param}"

    return (src_path, target_path, *tags)


@pytest.fixture(params=PARAMS_MULTIPLES)
def src_to_target_params_multiples_use_config(request) -> Iterator[Tuple[str, ...]]:
    config = configparser.ConfigParser()
    src_path = path_to_src_file_singles(request.param[0])
    target_path = path_to_target_file_singles(request.param[1])

    config_path = f"{TEST_FILES_PATH}/test.ini"

    section = {
        "path": src_path,
        "config_path": config_path,
        "tags": ','.join(request.param[2:])
    }

    config["pytagged"] = section

    # write config
    with open(config_path, 'w') as f:
        config.write(f)

    yield config_path, target_path
    os.remove(config_path)


@pytest.fixture
def cleanup_test_path_multiples() -> Iterator[int]:
    src_path = Path(f"{TEST_FILES_PATH}/multiples/src/")
    src_files = list(src_path.glob("*.py"))
    src_contents = {}
    for f in src_files:
        fname = str(f)
        with f.open() as fin:
            src_contents[fname] = fin.read()

    yield 1

    for f in src_files:
        fname = str(f)
        with f.open('w') as fout:
            fout.write(src_contents[fname])


@pytest.fixture
def cleanup_test_path_singles() -> Iterator[int]:
    src_path = Path(f"{TEST_FILES_PATH}/singles/src/")
    src_files = list(src_path.glob("*.py"))
    src_contents = {}
    for f in src_files:
        fname = str(f)
        with f.open() as fin:
            src_contents[fname] = fin.read()

    yield 1

    for f in src_files:
        fname = str(f)
        with f.open('w') as fout:
            fout.write(src_contents[fname])
