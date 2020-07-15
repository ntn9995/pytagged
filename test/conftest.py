from pathlib import Path
from typing import Tuple, Generator
from string import Template

import pytest


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


@pytest.fixture(scope="module", params=PARAMS)
def src_to_target_params(request) -> Tuple[str, ...]:

    src_path = path_to_src_file_singles(request.param[0])
    target_path = path_to_target_file_singles(request.param[1])

    return (src_path, target_path, *request.param[2:])


@pytest.fixture(scope="module", params=PARAMS_MULTIPLES)
def src_to_target_params_multiples(request) -> Tuple[str, ...]:
    src_dir_param = request.param[0]
    target_dir_param = request.param[1]
    tags = request.param[2:]
    parent_path = path_to_multiples()
    src_path = f"{parent_path}/{src_dir_param}"
    target_path = f"{parent_path}/{target_dir_param}"

    return (src_path, target_path, *tags)


@pytest.fixture
def cleanup_test_path_multiples() -> Generator[int, None, None]:
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
def cleanup_test_path_singles() -> Generator[int, None, None]:
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
