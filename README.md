PyTagged
========
![ci-workflow](https://github.com/ntn9995/pytagged/workflows/ci-workflow/badge.svg?branch=master)

## What is it?
PyTagged is a simple CLI utlity written in python that helps you comment out "tagged" code. For a simple example, this might be a common pattern in your code.
```python
def production_code():
    while True:
        expensive_debug_code()  # debug
        prod_code()
```

While this fine for most cases (), it's a wasted instruction for every iteration of the
and we all know how expensive function calls are in Python. What PyTagged helps you with is to turn the above code to.

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


## More usage and example
### TBA
