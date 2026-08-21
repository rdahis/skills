#!/usr/bin/env python3
r"""Accept or reject markup-mode suggestions in LaTeX files.

Constructs handled (see reference/markup-mode.md):

  inline   \added{X}  \deleted{X}  \replaced{new}{old}  \highlight{X}
  blocks   %% >>> SUGGEST ADD <label> >>>  ...  %% <<< SUGGEST END <<<
           %% >>> SUGGEST DEL <label> >>>  ...  %% <<< SUGGEST END <<<

                       --accept                --reject
  \added{X}            X                       (removed)
  \deleted{X}          (removed)               X
  \replaced{new}{old}  new                     old
  \highlight{X}        X                       X
  SUGGEST ADD block    body kept               (removed)
  SUGGEST DEL block    (removed)               body uncommented

Usage:
  resolve-markup.py FILE...  --list
  resolve-markup.py FILE...  --accept  [--label L] [--dry-run] [--no-backup]
  resolve-markup.py FILE...  --reject  [--label L] [--dry-run] [--no-backup]

--label restricts block resolution to blocks carrying that label; inline macros
carry no label and are left untouched when --label is given.

Refuses to modify a file containing an unterminated block, a nested block, or an
unbalanced macro argument, rather than guessing.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OPEN_RE = re.compile(r"^[ \t]*%%[ \t]*>>>[ \t]*SUGGEST[ \t]+(ADD|DEL)\b[ \t]*(.*?)[ \t]*>>>[ \t]*$")
CLOSE_RE = re.compile(r"^[ \t]*%%[ \t]*<<<[ \t]*SUGGEST[ \t]+END[ \t]*<<<[ \t]*$")

ONE_ARG = ("added", "deleted", "highlight")
TWO_ARG = ("replaced",)
MAX_PASSES = 10


class MarkupError(Exception):
    pass


# --------------------------------------------------------------------------- #
# comment mask
# --------------------------------------------------------------------------- #

def comment_mask(text: str) -> list[bool]:
    """True at every index that sits inside a LaTeX comment."""
    mask = [False] * len(text)
    in_comment = False
    backslashes = 0
    for i, ch in enumerate(text):
        if ch == "\n":
            in_comment = False
            backslashes = 0
            continue
        if in_comment:
            mask[i] = True
            continue
        if ch == "%" and backslashes % 2 == 0:
            in_comment = True
            mask[i] = True
        backslashes = backslashes + 1 if ch == "\\" else 0
    return mask


def read_group(text: str, open_idx: int, mask: list[bool]) -> tuple[str, int]:
    """Read a braced group starting at `open_idx` ('{'). Returns (body, end).

    `end` is the index just past the closing brace. Braces inside comments and
    escaped braces do not count.
    """
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if mask[i] or (i > 0 and text[i - 1] == "\\" and not (i > 1 and text[i - 2] == "\\")):
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i], i + 1
        i += 1
    raise MarkupError(f"unbalanced braces starting at offset {open_idx}")


# --------------------------------------------------------------------------- #
# inline macros
# --------------------------------------------------------------------------- #

def find_inline(text: str) -> list[tuple[int, str]]:
    """Positions of markup macros outside comments: (index, macro name)."""
    mask = comment_mask(text)
    hits = []
    for name in ONE_ARG + TWO_ARG:
        token = "\\" + name + "{"
        start = 0
        while True:
            i = text.find(token, start)
            if i < 0:
                break
            start = i + 1
            if mask[i]:
                continue
            # a preceding backslash means the control sequence is escaped
            if i > 0 and text[i - 1] == "\\":
                continue
            hits.append((i, name))
    return sorted(hits)


def resolve_inline_once(text: str, accept: bool) -> tuple[str, int]:
    mask = comment_mask(text)
    hits = find_inline(text)
    if not hits:
        return text, 0

    out = []
    cursor = 0
    count = 0
    for idx, name in hits:
        if idx < cursor:                       # already consumed inside an outer group
            continue
        brace = idx + len(name) + 1            # the '{' after the macro name
        first, end = read_group(text, brace, mask)
        if name in TWO_ARG:
            while end < len(text) and text[end] in " \t\n" :
                end += 1
            if end >= len(text) or text[end] != "{":
                raise MarkupError(rf"\{name} at offset {idx} needs two arguments")
            second, end = read_group(text, end, mask)
        else:
            second = ""

        if name == "added":
            repl = first if accept else ""
        elif name == "deleted":
            repl = "" if accept else first
        elif name == "highlight":
            repl = first
        else:                                   # replaced{new}{old}
            repl = first if accept else second

        out.append(text[cursor:idx])
        out.append(repl)
        cursor = end
        count += 1

    out.append(text[cursor:])
    return "".join(out), count


def resolve_inline(text: str, accept: bool) -> tuple[str, int]:
    total = 0
    for _ in range(MAX_PASSES):
        text, n = resolve_inline_once(text, accept)
        total += n
        if n == 0:
            break
    return text, total


# --------------------------------------------------------------------------- #
# blocks
# --------------------------------------------------------------------------- #

def parse_blocks(lines: list[str]) -> list[tuple[int, int, str, str]]:
    """(start, end, kind, label) for each block; indices are line numbers."""
    blocks = []
    i = 0
    while i < len(lines):
        m = OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        kind, label = m.group(1), m.group(2).strip()
        j = i + 1
        while j < len(lines):
            if OPEN_RE.match(lines[j]):
                raise MarkupError(f"line {j + 1}: SUGGEST block opened inside another block")
            if CLOSE_RE.match(lines[j]):
                break
            j += 1
        if j >= len(lines):
            raise MarkupError(f"line {i + 1}: SUGGEST {kind} block never closed")
        blocks.append((i, j, kind, label))
        i = j + 1
    return blocks


def resolve_blocks(text: str, accept: bool, label: str | None) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    blocks = parse_blocks(lines)
    if not blocks:
        return text, 0

    drop = set()
    out = list(lines)
    count = 0
    for start, end, kind, blabel in blocks:
        if label is not None and blabel != label:
            continue
        count += 1
        drop.add(start)
        drop.add(end)
        keep_body = (kind == "ADD") == accept
        if not keep_body:
            drop.update(range(start + 1, end))
        elif kind == "DEL":                     # rejected deletion: uncomment
            for k in range(start + 1, end):
                if out[k].startswith("%"):
                    out[k] = out[k][1:]

    result = "".join(line for k, line in enumerate(out) if k not in drop)
    return result, count


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #

def summarise(path: Path) -> None:
    text = path.read_text()
    try:
        blocks = parse_blocks(text.splitlines(keepends=True))
    except MarkupError as e:
        print(f"{path}: ERROR {e}")
        return
    inline = find_inline(text)
    if not blocks and not inline:
        print(f"{path}: no markup")
        return
    print(f"{path}:")
    for start, end, kind, label in blocks:
        span = end - start - 1
        print(f"  line {start + 1:>5}  SUGGEST {kind}  {span} line(s)  {label or '(no label)'}")
    if inline:
        tally: dict[str, int] = {}
        for _, name in inline:
            tally[name] = tally.get(name, 0) + 1
        print("  inline: " + ", ".join(f"\\{k} x{v}" for k, v in sorted(tally.items())))


def main() -> int:
    ap = argparse.ArgumentParser(description="Accept or reject markup-mode suggestions.")
    ap.add_argument("files", nargs="+", type=Path)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--accept", action="store_true")
    mode.add_argument("--reject", action="store_true")
    mode.add_argument("--list", action="store_true")
    ap.add_argument("--label", help="only resolve blocks carrying this label")
    ap.add_argument("--dry-run", action="store_true", help="report, do not write")
    ap.add_argument("--no-backup", action="store_true", help="skip writing FILE.bak")
    args = ap.parse_args()

    missing = [f for f in args.files if not f.is_file()]
    if missing:
        for f in missing:
            print(f"no such file: {f}", file=sys.stderr)
        return 2

    if args.list:
        for f in args.files:
            summarise(f)
        return 0

    accept = args.accept
    failed = False
    for f in args.files:
        original = f.read_text()
        try:
            text, nblocks = resolve_blocks(original, accept, args.label)
            ninline = 0
            if args.label is None:
                text, ninline = resolve_inline(text, accept)
        except MarkupError as e:
            print(f"{f}: refused — {e}", file=sys.stderr)
            failed = True
            continue

        verb = "accept" if accept else "reject"
        if nblocks == 0 and ninline == 0:
            print(f"{f}: nothing to {verb}")
            continue
        if text == original:
            print(f"{f}: no change")
            continue
        if args.dry_run:
            print(f"{f}: would {verb} {nblocks} block(s), {ninline} inline macro(s)")
            continue
        if not args.no_backup:
            f.with_suffix(f.suffix + ".bak").write_text(original)
        f.write_text(text)
        print(f"{f}: {verb}ed {nblocks} block(s), {ninline} inline macro(s)"
              + ("" if args.no_backup else f"  (backup: {f.name}.bak)"))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
