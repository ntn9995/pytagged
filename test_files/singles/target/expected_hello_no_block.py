if __name__ == "__main__":
    print("Hello world")
    # print("Hello debug world")  # debug
    # print("Hello skip world")  # skip
    # print("hello slow world")  # slow

    # block: slow
    # print("Whatever so slow") # slow
    # assert 0    # debug

    # block: debug
    # assert __debug__    # skip
    while True:
        print("Debug")

    # assert 1    # debug
