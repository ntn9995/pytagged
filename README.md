PyTagged: Automatic Comment CLI
===============================
![ci-workflow](https://github.com/ntn9995/pytagged/workflows/ci-workflow/badge.svg?branch=master)(https://github.com/ntn9995/pytagged/actions?query=workflow%3Aci-workflow)

## What is it?
PyTagged is a simple CLI utlity written in python that helps you comment out "tagged" code. For a simple example, this might be a common pattern in your code.
```python
def production_code():
    while True:
        expensive_debug_code()  # debug
        prod_code()
```

While this fine for most cases, it's a wasted instruction/call every iteration of the loop,
and this can get expensive fast. With PyTagged you can do this `pytag production.py -t debug`, and the above code would become:
```python
def production_code():
    while True:
        # expensive_debug_code()  # debug
        prod_code()
```

Fairly straight forward, just comment out lines that end with a "tag", in this case:
'# debug'. PyTagged can also do this with "tagged blocks", turning this:

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

While these example are fairly trivial, PyTagged is flexible and lets you define your own "tags" to support more complex use cases.


## Usage & example

### Multiple files
PyTagged accepts its first argument as a path, if the path is a directory, it recursively
scans for all '.py' files within that directory (and the subdirectories). By default, PyTagged works on the cwd. So if your project looks like this:
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
PyTagged ignores certain cases to avoid any unecessary modifications.


### Already commented lines
PyTagged ignores already commented lines, even if they are inlined tagged or block tagged. Take this code.

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
An opened block starts with `# block: tag` but does not have a closing `# end`. PyTagged
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

## Misc

### Modes:
PyTagged can run in either:
1. default mode: works on files, prints no output
2. printonly: does NOT modify files, prints raw string output of would-be modified files
3. benchmark: copies files to temp files, work on the temp files, and prints out some performance statistics
4. verbose: works on files, prints out some output
