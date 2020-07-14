def fn_with_docstring():
    """This should not be commented out         # debug
    we don't do anything in a triple quote      # debug
    block if the start of that block is the     # debug
    start of a line.                            # debug
    """

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
