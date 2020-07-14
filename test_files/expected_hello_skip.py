if __name__ == "__main__":
    """some docstring   # slow
    """
    print("Hello world")
    print("Hello debug world")  # debug
    # print("Hello skip world")  # skip
    print("hello slow world")  # slow

    # print("already commented ") # slow
    # print("same") # debug
    assert 0    # debug

    # block: slow
    # assert __debug__    # skip
    while True:
        print("Debug")

    1 + 1
    2 + 2
    s = "somestr"
    # end

    # block: skip

    # assert 1

    # end
