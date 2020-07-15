from pathlib import Path
from typing import Tuple
from string import Template

import pytest


TEST_FILES_PATH = "./test_files"
PARAMS = [("hello.py", "expected_hello.py", "debug"),
          ("hello.py", "expected_hello_skip.py", "skip"),
          ("hello.py", "expected_hello_slow.py", "slow"),
          ("hello_no_block.py", "expected_hello_no_block.py",
           "debug", "skip", "slow"),
          ("triple_quote.py", "expected_triple_quote.py", "debug"),
          ("fake_block.py", "expected_fake_block.py", "debug")]

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


@pytest.fixture(scope="module")
def test_files_path() -> str:
    return TEST_FILES_PATH


@pytest.fixture(scope="module")
def test_files_path_singles() -> str:
    return f"{TEST_FILES_PATH}/singles"


@pytest.fixture(scope="module")
def test_files_path_multiples() -> str:
    return f"{TEST_FILES_PATH}/multiples"


@pytest.fixture(scope="module", params=PARAMS)
def src_to_target_params(request) -> Tuple[str, ...]:

    src_path = path_to_src_file_singles(request.param[0])
    target_path = path_to_target_file_singles(request.param[1])

    return (src_path, target_path, *request.param[2:])


@pytest.fixture(params=PARAMS)
def src_to_target_params_with_cleanup(request) -> Tuple[str, ...]:
    src_fname, target_fname = request.param[0], request.param[1]
    src_path_str = path_to_src_file_singles(src_fname)
    with open(src_path_str) as f:
        content_og = f.read()

    target_path_str = path_to_target_file_singles(target_fname)
    args = (src_path_str, target_path_str, *request.param[2:])

    yield args

    # restore file content
    with open(src_path_str, 'w') as f:
        f.write(content_og)


@pytest.fixture
def test_path_multiples_with_cleanup() -> Path:
    test_path = Path(f"{TEST_FILES_PATH}/multiples/")
    src_files = list(test_path.glob(r"src/*.py"))

    print([str(f) for f in src_files])

    src_contents = {}

    for f in src_files:
        fname = str(f)
        with f.open() as fin:
            src_contents[fname] = fin.read()

    yield test_path

    for f in src_files:
        fname = str(f)
        with f.open('w') as fout:
            fout.write(src_contents[fname])
