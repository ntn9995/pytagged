import subprocess

from pytagged.utils import print_raw_lines, pretty_print_title


def test_cli_singles(src_to_target_params_with_cleanup):
    src_path = src_to_target_params_with_cleanup[0]
    target_path = src_to_target_params_with_cleanup[1]
    tags = src_to_target_params_with_cleanup[2:]

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


def test_cli_multiples(test_path_multiples_with_cleanup):

    path = test_path_multiples_with_cleanup
    cmd = ["pytag", path, "-t", "debug"]

    print(cmd)
    subprocess.run(cmd, check=True)

    target_files = set(path.glob(r"expected*.py"))
    src_files = set(path.glob(r"*.py")) - target_files

    expected_contents = {}
    for f in target_files:
        fname = str(f).split('/')[-1]
        with f.open() as fin:
            expected_contents[fname] = fin.readlines()

    actual_contents = {}
    for f in src_files:
        fname = str(f).split('/')[-1]
        with f.open() as fin:
            actual_contents[fname] = fin.readlines()

    for name in actual_contents:
        actual = actual_contents[name]
        expected = expected_contents[f"expected_{name}"]
        assert actual == expected
