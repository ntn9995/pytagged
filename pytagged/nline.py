import re
from typing import IO, List, Iterable

TRIPLE_QUOTE = '"""'
TRIPLE_QUOTE_SINGLE = "'''"


def get_newlines(file: IO, tags: Iterable[str]) -> List[str]:

    tags_match_str = '|'.join(tags)
    inline_rgx = re.compile(
        rf"^(?!.*({TRIPLE_QUOTE}|{TRIPLE_QUOTE_SINGLE})).*# ({tags_match_str})$")
    cmt_line_rgx = re.compile(r"\s*#")
    block_start_rgx = re.compile(rf"\s*# block: ({tags_match_str})")
    block_end_rgx = re.compile(r"# end$")
    triple_quote_rgx = re.compile(rf"\s*({TRIPLE_QUOTE}|{TRIPLE_QUOTE_SINGLE})")
    triple_quote_end_rgx = re.compile(rf"({TRIPLE_QUOTE}|{TRIPLE_QUOTE_SINGLE})$")

    cur_block_start_idx = -1
    cur_triple_quote_block_start_idx = -1
    indices = set()
    cmt_line_idx = set()
    block_pairs = []
    triple_quote_pairs = []
    lines = []

    readlines = enumerate(file)

    for i, ln in readlines:
        lines.append(ln)
        if cmt_line_rgx.match(ln):
            cmt_line_idx.add(i)

        if inline_rgx.search(ln):
            indices.add(i)

        if block_end_rgx.search(ln):
            block_pairs.append((cur_block_start_idx, i))
            cur_block_start_idx = -1
            continue

        if triple_quote_end_rgx.search(ln):
            triple_quote_pairs.append((cur_triple_quote_block_start_idx, i))
            cur_triple_quote_block_start_idx = -1
            continue

        if block_start_rgx.match(ln):
            cur_block_start_idx = i
            continue

        if triple_quote_rgx.match(ln):
            cur_triple_quote_block_start_idx = i
            continue

    for start, end in block_pairs:
        if start == -1:
            continue
        _range = range(start + 1, end)
        indices |= {j for j in _range}

    for start, end in triple_quote_pairs:
        if start == -1:
            continue
        _range = range(start, end + 1)
        indices -= {j for j in _range}

    indices -= cmt_line_idx

    for i in indices:
        line = lines[i]
        if line == '\n':
            continue
        for j, c in enumerate(line):
            if c != ' ':
                break
        lines[i] = f"{line[:j]}# {line[j:]}"

    return lines
