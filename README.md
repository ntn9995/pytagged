pytagged: Auto Comment CLI
===============================
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/ntn9995/pytagged/ci-workflow?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytagged?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/pytagged?color=blue&style=flat-square)

## What is it?
pytagged is a simple CLI utlity written in python that helps you comment out "tagged" code. For a simple example, this might be a common pattern in your code.
```python
def production_code():
    while True:
        expensive_debug_code()  # debug
        prod_code()
```

While this fine for most cases, it's a wasted instruction/call every iteration of the loop,
and this can get expensive fast. With pytagged you can do this `pytag production.py -t debug`, and the above code would become:
```python
def production_code():
    while True:
        # expensive_debug_code()  # debug
        prod_code()
```

Fairly straight forward, just comment out lines that end with a "tag", in this case:
'# debug'. pytagged can also do this with "tagged blocks", turning this:

```python
def production_code():
    while True:
        # block: debug
        expensive_debug_code_1()
        expensive_debug_code_2()
        ...
        expensive_debug_code_n()
        # end
        prod_code()
```

Into this:

```python
def production_code():
    while True:
        # block: debug
        # expensive_debug_code_1()
        # expensive_debug_code_2()
        # ...
        # expensive_debug_code_n()
        # end
        prod_code()
```

While these example are fairly trivial, pytagged is flexible and lets you define your own "tags" to support more complex use cases.


## Usage & example

### Installation

Simply use: `pip install pytagged`, or you can clone this directory and install pytagged directly by running `setup.py`.

Note that the source code (dev version) is a little different from the pypi distribution. Functionally, they're the same, the dev version just prints out more stuffs for my debugging purposes.

### Multiple files
pytagged accepts its first argument as a path, if the path is a directory, it recursively
scans for all '.py' files within that directory (and the subdirectories). By default, pytagged works on the cwd. So if your project looks like this:
```
.
├── requirements.txt
├── src
│   ├── __init__.py
│   └── main.py
└── test
    ├── test.dat
    └── test_main.py
```

Running `pytag -t debug` will affect the .py files in `./src/` and in `./test`.

### Multiple tags
Pytaggd accepts multiple tags. You just need to specify them using the -t flag. For example, running `pytag ./hello.py -t debug skip slow` on a file like this.

```python
if __name__ == "__main__":
    print("Hello world")
    print("Hello debug world")  # debug
    print("Hello skip world")  # skip
    print("hello slow world")  # slow
    assert 0    # debug

    # block: slow
    assert __debug__    # skip
    while True:
        print("Debug")

    1 + 1
    2 + 2
    s = "somestr"
    # end

    # block: skip

    assert 1

    # end

```

will turn it to:

```python
if __name__ == "__main__":
    print("Hello world")
    # print("Hello debug world")  # debug
    # print("Hello skip world")  # skip
    # print("hello slow world")  # slow
    # assert 0    # debug

    # block: slow
    # assert __debug__    # skip
    # while True:
        # print("Debug")

    # 1 + 1
    # 2 + 2
    # s = "somestr"
    # end

    # block: skip

    # assert 1

    # end

```

## Behaviors
pytagged ignores certain cases to avoid any unecessary modifications.


### Already commented lines
pytagged ignores already commented lines, even if they are inlined tagged or block tagged. Take this code.

```python
def some_fn():
    # print("already commented ") # slow
    # print("same") # debug
    print("debug")    # debug
```

The second and third lines will be ignored, even if you run `pytag file.py -t debug slow`,
resulting in:

```python
def some_fn():
    # print("already commented ") # slow
    # print("same") # debug
    # print("debug")    # debug
```

### Opened blocks
An opened block starts with `# block: tag` but does not have a closing `# end`. pytagged
ignores cases like this. For example, running `pytag file.py -t debug` on this:

```python
def opened_block():
    # block: debug
    print("This is an opened block")
    print("Inlined tag, this would still work")     # debug
    
    # block: debug
    print("This is a proper block")
 
    print("Below is the end block tag")
    # end
    return 0
```

would result in:

```python
def opened_block():
    # block: debug
    print("This is an opened block")
    # print("Inlined tag, this would still work")     # debug
    
    # block: debug
    # print("This is a proper block")
 
    # print("Below is the end block tag")
    # end
    return 0
```

### Triple quoted string/docstring
Triple quotes are either `'''` or `"""`

Triple quoted block, that is a block whose line starts with `"""` and ends with a line
with only `"""` is ignored.
Lines that have triple quoted strings in them, but do not start with `"""` can be commented
out with block tags, but not inlined tags.

Running `pytag file.py -t debug` on:

```python
def fn_with_docstring():
    '''This should not be commented out         # debug
    we don't do anything in a triple quote      # debug
    block if the start of that block is the     # debug
    start of a line.                            # debug
    '''

    some_str = "this should be commented out normally"  # debug

    # block: debug
    triple_quote_str = """This however would be commented out
    if it's block tagged"""
    # end

    triple_quote_str = """But triple quote strings can't be commented   # debug
    out using inline tags"""

    # block: debug
    """This should not be commented out, even if it's block tagged
    """
    # end

    return triple_quote_str

```

would result in:

```python
def fn_with_docstring():
    '''This should not be commented out         # debug
    we don't do anything in a triple quote      # debug
    block if the start of that block is the     # debug
    start of a line.                            # debug
    '''

    # some_str = "this should be commented out normally"  # debug

    # block: debug
    # triple_quote_str = """This however would be commented out
    # if it's block tagged"""
    # end

    triple_quote_str = """But triple quote strings can't be commented   # debug
    out using inline tags"""

    # block: debug
    """This should not be commented out, even if it's block tagged
    """
    # end

    return triple_quote_str

```

## More advanced usage

### Exclude patterns
By default, pytagged ignore files/directories that match against any of these patterns:
`".svn", "CVS", ".bzr", ".hg", ".git", "__pycache__", ".tox", ".eggs", "*.egg"`.

You can override this through the -x/--exclude flag. For example: `pytag . -t debug -x env` will ignore any files  or directories (along with all the subdirectories and files in them) with the name 'env'. This is useful for things like ignoring python packages in a virtual environment. 

Another option is to use the -xt/--extend-exclude flag to add more patterns to the excluded patterns like this `pytag . -t debug --xt env`. This will add 'env' to the default excluded patterns. If you use both  -x and --xt at the same time, the resulting excluded patterns will be the union set of the two.

### Config file
Every command line flag (except for -cf/--config) can be configured in a .ini format compliant file like this:

```
[pytagged]

path = pytagged
tags =
    debug,
    develop
# tags = debug, develop     this also works
exclude = env, test*
```

To tell pytagged to use the config file you can use the -cf/--config flag: `pytag -cf [config_path]`, or you just use `pytag` and name your file 'pytagged.ini' and place it at the current directory, which is the default location that pytagged looks for the config file when it's run with no command line arguments. Note that you have to have the options declared under the `pytagged` header/session as in the example, as pytagged will only read configurations from there.

You can also use command line arguments in combination with a config file: take the file 'pytagged.ini' from the previous example, and:
```bash
pytag --config pytagged.ini -xt build
```

Running this is equivalent to:
```bash
pytag pytagged -t debug develop -x env test* -xt build
```

In this scenario, the `path, tags, exclude` options are provided by the config file, while the `-xt` flag from the command line provides argument for the `extend-exclude` option. Note that the arguments from the cli take precedence over options from the config file.

By default, if no config path is provided, pytagged looks for the default `pytagged.ini` file. If one exists, pytagged will use the options provided there as a base and update/override them with options from the command line as appropriate.

## Misc

### Modes
There are 3 modes that pytagged runs in:
1. Default: No output
2. Printonly: does NOT modify files, but instead print the raw string output of what the modified files would be
3. Benchmark: Performs a benchmark of n runs (defaults to 100, configurable through cli or config file), and prints out performance statistics of the phases in processing the files.

Note: You can also use the -v/--verbose flag to print out some more info.