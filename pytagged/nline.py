import re
from typing import IO, List

POUND = '#'
BLOCK_START = "# block:"
BLOCK_END = "# end"
TRIPLE_QUOTE = '"""'
TRIPLE_QUOTE_SINGLE = "'''"


def get_newlines(file: IO, tag: str, *tags: str) -> List[str]:

    if not tag or tag == ' ':
        raise ValueError("Tags cannot be an empty string or a whitepsace")

    for t in tags:
        if not t or t == ' ':
            raise ValueError("Tags cannot be an empty string or a whitepsace")

    tags_match_str = tag

    if len(tags) > 0:
        tags_match_str += '|' + '|'.join(tags)

    line_split_rgx = re.compile(r"^(?!\s*$)(\s*)(.+)")
    block_start_rgx = re.compile(rf"{BLOCK_START} ({tags_match_str})")
    triple_quote_rgx = re.compile(rf"{TRIPLE_QUOTE}|{TRIPLE_QUOTE_SINGLE}")
    inline_rgx = re.compile(
        rf"^(?!{POUND})(?!.*({TRIPLE_QUOTE}|{TRIPLE_QUOTE_SINGLE})).*{POUND} ({tags_match_str})$")  # noqa: E501
    # monotonic_time = time.monotonic
    cur_block_start_idx = -1
    cur_triple_quote_start_idx = -1
    indices = set()
    block_pairs = []
    triple_quote_pairs = []
    matches = []
    newlines = []
    cmt_lines = []

    # line_scan_st = monotonic_time()
    # inline_scan_dur = 0
    # split_line_dur = 0
    for i, ln in enumerate(file):
        # st = monotonic_time()
        newlines.append(ln)
        matched = line_split_rgx.search(ln)
        # split_line_dur += 1000 * (monotonic_time() - st)
        matches.append(matched)
        if not matched:
            continue
        non_whitespace = matched.group(2)
        if non_whitespace[0] == POUND:
            cmt_lines.append(i)

        # st = monotonic_time()
        if inline_rgx.search(non_whitespace):
            indices.add(i)
        # inline_scan_dur += 1000 * (monotonic_time() - st)

        if non_whitespace == BLOCK_END:
            block_pairs.append((cur_block_start_idx, i))
            cur_block_start_idx = -1
            continue

        if non_whitespace in (TRIPLE_QUOTE, TRIPLE_QUOTE_SINGLE):
            triple_quote_pairs.append((cur_triple_quote_start_idx, i))
            cur_triple_quote_start_idx = -1
            continue

        if block_start_rgx.match(non_whitespace):
            cur_block_start_idx = i
            continue

        if triple_quote_rgx.match(non_whitespace):
            cur_triple_quote_start_idx = i
            continue

    """ line_scan_dur = 1000 * (monotonic_time() - line_scan_st)
    print(f"Time taken for scanning lines & computing indices: \
        {line_scan_dur:.2f} ms")
    print(f"Time taken for rgx splitting: {split_line_dur:.2f} ms")
    print(f"Time taken for inline rgx match: {inline_scan_dur:.2f} ms") """

    # update block indices
    for idx in block_pairs:
        start, end = idx
        if start == -1:
            continue
        indices |= {j for j in range(start + 1, end) if j not in cmt_lines}

    # remove triple quote block indices
    for idx in triple_quote_pairs:
        start, end = idx
        if start == -1:
            continue
        indices -= {j for j in range(start, end + 1)}

    for i, matched in enumerate(matches):
        if not matched:
            continue
        if i not in indices:
            continue
        newlines[i] = matched.expand(r"\g<1># \g<2>\n")

    return newlines
