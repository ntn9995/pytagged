from pathlib import Path
import subprocess


from pytagged._utils import print_raw_lines, pretty_print_title


def test_cli_singles(cleanup_test_path_singles, src_to_target_params):
    src_path = src_to_target_params[0]
    target_path = src_to_target_params[1]
    tags = src_to_target_params[2:]

    cmd = ["pytag", src_path, "-t", *tags]
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


def test_cli_multiples(cleanup_test_path_multiples, src_to_target_params_multiples):

    src_path, target_path = src_to_target_params_multiples[:2]
    tags = src_to_target_params_multiples[2:]
    cmd = ["pytag", src_path, "-t", *tags]

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
