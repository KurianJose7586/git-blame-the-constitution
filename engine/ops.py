"""Edit operations and the executor that applies them to law files (KICKOFF.md T14; decision 9).

A law is a dict {path: text} of files in contract 2's format. An operation is a dict:

    {"op": "SUBSTITUTE_WORDS", "target": "s.13(1)", "old": "...", "new": "..."}

Targets are cited the way lawyers cite them: a file (`art.15`, `s.13`, `sch.2`, `preamble`) followed by labels
(`s.8(1)(j)`, `sch.2(8)`) and, for unlabelled provisions, `/proviso`, `/proviso2`, `/explanation`. A block is the
amending text's own lines, one provision per line; `structure()` works out depth and formatting.
"""
import difflib
import re
from pathlib import PurePosixPath

OPS = {  # op -> its fields besides "op"; engine/ops.schema.json says the same for constrained decoding
    "SUBSTITUTE_WORDS": ("target", "old", "new"),
    "INSERT_WORDS": ("target", "position", "anchor", "text"),
    "OMIT_WORDS": ("target", "text"),
    "SUBSTITUTE_NODE": ("target", "block"),
    "INSERT_NODE": ("target", "position", "block"),
    "ADD_AT_END": ("target", "block"),
    "OMIT_NODE": ("target",),
    "RENUMBER": ("target", "label"),
}
ITEM = re.compile(r"^( *)- (.*)$")
LABEL = re.compile(r"^\(([0-9]+[A-Z]*|[a-z]{1,6}|[A-Z])\)(?:\s|$)|^([0-9]+[A-Z]*)\.\s")  # "(2)" alone: "(2)(a) ..."
FILE_ID = re.compile(r"^(preamble|art\.\d+[A-Z]*|s\.\d+[A-Z]*|sch\.\d+)")


class EditError(ValueError):
    pass


def file_id(path):
    name = PurePosixPath(path).stem
    if name == "preamble":
        return "preamble"
    m = re.fullmatch(r"(article|section|schedule)-0*(\d+)([a-z]*)", name)
    return m and {"article": "art.", "section": "s.", "schedule": "sch."}[m[1]] + m[2] + m[3].upper()


def nodes(text):
    """Every list item of a file as (id suffix, first line, end line, depth): lines[first:end] is its subtree."""
    lines, out, path, seen = text.split("\n"), [], [], {}
    for i, line in enumerate(lines):
        m = ITEM.match(line)
        if not m:
            continue
        depth, body = len(m[1]) // 2, m[2]
        path = [p for p in path if p[0] < depth]
        label = LABEL.match(body)
        if label:
            seg = f"({label[1] or label[2]})"
        else:
            kind = "proviso" if body.startswith("*Provided") else "explanation" if body.startswith("*Explanation") else "para"
            key = ("".join(s for _, s in path), kind)
            seen[key] = seen.get(key, 0) + 1
            seg = f"/{kind}{seen[key] if seen[key] > 1 else ''}"
        path.append((depth, seg))
        end = i + 1
        while end < len(lines) and (n := ITEM.match(lines[end])) and len(n[1]) // 2 > depth:
            end += 1
        out.append(("".join(s for _, s in path), i, end, depth))
    return out


def find(files, target):
    """(path, first, end, depth) of the target; first is None when the target is a whole file."""
    m = FILE_ID.match(target)
    path = m and next((p for p in files if file_id(p) == m[1]), None)
    if not path:
        raise EditError(f"{target}: no such provision (files: {', '.join(sorted(filter(None, map(file_id, files))))})")
    rest = target[m.end():]
    if not rest:
        return path, None, None, -1
    hits = [n for n in nodes(files[path]) if n[0] == rest]
    if not hits:
        near = difflib.get_close_matches(rest, [n[0] for n in nodes(files[path])], n=3, cutoff=0.4)
        raise EditError(f"{target}: not found in {path}" + (f"; nearest: {', '.join(m[1] + n for n in near)}" if near else ""))
    return (path, *hits[0][1:])


def nearest(needle, hay):
    words, n = hay.split(), len(needle.split())
    spans = {" ".join(words[i:i + n]) for i in range(max(1, len(words) - n + 1))}
    best = difflib.get_close_matches(needle, spans, n=1, cutoff=0.5)
    return f"; nearest is {best[0]!r}" if best else ""


# --- Blocks: the amending text's lines, given their depth and our formatting -------------------------------

ROMAN = re.compile(r"^(?=[ivx])x{0,3}(ix|iv|v?i{0,3})$")


def follows(label, last):
    if label.startswith(last):  # an inserted label: (ca) after (c), (4A) after (4)
        return True
    if label.isdigit() and last.rstrip("ABCDEFGH").isdigit():
        return int(label) == int(last.rstrip("ABCDEFGH")) + 1
    return len(label) == 1 and len(last) <= 2 and ord(label) == ord(last[0]) + 1


def kind(label, stack, nxt):
    if label[0].isdigit():
        return "num"
    if label.isupper():
        return "Alpha"
    if ROMAN.match(label):  # (i) is clause i only after (h), and only if (ii) doesn't come next
        after_alpha = any(k == "alpha" and follows(label, last) for k, last in stack)
        return "alpha" if after_alpha and nxt != {"i": "ii", "v": "vi", "x": "xi"}.get(label) else "roman"
    return "alpha"


def structure(block, schedule=False):
    """[(depth, line)] for a block, depth relative to its first provision, in contract 2's formatting."""
    lines = [" ".join(l.split()) for l in block.split("\n") if l.strip()]
    matches = [LABEL.match(l) for l in lines]
    labels = [(m[1] or m[2]) if m else None for m in matches]
    out, stack = [], []
    for n, line in enumerate(lines):
        if labels[n]:
            label = labels[n]
            # "2." (a Schedule's paragraph or entry) and "(2)" (its sub-paragraph) are different lists
            dotted = bool(matches[n][2]) and not schedule
            k = "para" if dotted else kind(label, stack, next((x for x in labels[n + 1:] if x), None))
            levels = [i for i, s in enumerate(stack) if s[0] == k]
            fits = [i for i in reversed(levels) if follows(label, stack[i][1])]
            depth = fits[0] if fits else levels[-1] if levels and label not in ("1", "a", "i", "A") else len(stack)
            stack = stack[:depth] + [(k, label)]
            if schedule:
                line = re.sub(r"^\((\d+[A-Z]*)\)\s", r"\1. ", line)  # "(15) Sashtra Seema Bal." -> "15. Sashtra Seema Bal."
        elif line.startswith(("Provided", "Explanation")):
            num = next((i for i, s in enumerate(stack) if s[0] == "num"), None)
            depth = num + 1 if num is not None else len(stack)
            line = re.sub(r"^(Provided(?: further| also)? that)", r"*\1*", line)
            line = re.sub(r"^Explanation", "*Explanation*", line)
        else:
            depth = len(stack)
        out.append((depth, line))
    return out


def render(block, depth, schedule):
    return [f"{'  ' * (depth + d)}- {line}" for d, line in structure(block, schedule)]


# --- The executor -----------------------------------------------------------------------------------------

def apply(files, ops):
    for op in ops:
        files = apply_one(files, op)
    return files


def apply_one(files, op):
    name = op.get("op")
    if name not in OPS or set(op) != {"op", *OPS[name]}:
        raise EditError(f"{op}: expected {name} with fields {OPS.get(name)}")
    target = op["target"]
    path, first, end, depth = find(files, target)
    lines = files[path].split("\n")
    if first is None:  # a whole file: everything after the heading
        first = 1 if lines[0].startswith("# ") else 0
        end = len(lines) - (lines[-1] == "")
    region = "\n".join(lines[first:end])
    schedule = path.startswith("schedule")

    if name in ("SUBSTITUTE_WORDS", "OMIT_WORDS", "INSERT_WORDS"):
        needle = op["old"] if name == "SUBSTITUTE_WORDS" else op["anchor"] if name == "INSERT_WORDS" else op["text"]
        if needle not in region:
            raise EditError(f"{name} {target}: {needle!r} not found{nearest(needle, region)}")
        if name == "SUBSTITUTE_WORDS":
            region = region.replace(needle, op["new"])
        elif name == "INSERT_WORDS":
            if op["position"] not in ("after", "before"):
                raise EditError(f"{name} {target}: position must be 'after' or 'before'")
            region = region.replace(needle, f"{needle} {op['text']}" if op["position"] == "after" else f"{op['text']} {needle}")
        else:
            region = region.replace(f" {needle}", "") if f" {needle}" in region else region.replace(needle, "")
        new = region.split("\n")
    elif name == "OMIT_NODE":
        new = []
    elif name == "RENUMBER":
        old = LABEL.match(ITEM.match(lines[first])[2]) if depth >= 0 else None
        if not old:
            raise EditError(f"{name} {target}: has no label to renumber")
        new =[lines[first].replace(old[0], f"({op['label']}) " if old[1] else f"{op['label']}. ", 1), *lines[first + 1:end]]
    elif depth < 0 and name != "ADD_AT_END":
        raise EditError(f"{name} {target}: names a whole file; name a provision in it")
    elif name == "SUBSTITUTE_NODE":
        new = render(op["block"], depth, schedule)
    elif name == "INSERT_NODE":
        if op["position"] not in ("after", "before"):
            raise EditError(f"{name} {target}: position must be 'after' or 'before'")
        block = render(op["block"], depth, schedule)
        new = [*lines[first:end], *block] if op["position"] == "after" else [*block, *lines[first:end]]
    else:  # ADD_AT_END: the block becomes the target's last children (or the file's last provisions)
        new = [*lines[first:end], *render(op["block"], depth + 1, schedule)]
    return {**files, path: "\n".join([*lines[:first], *new, *lines[end:]])}
