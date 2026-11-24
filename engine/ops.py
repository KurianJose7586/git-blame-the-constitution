"""Edit operations and the executor that applies them to law files (KICKOFF.md T14; decision 9).

A law is a dict {path: text} of files in contract 2's format. An operation is a dict:

    {"op": "SUBSTITUTE_WORDS", "target": "s.13(1)", "old": "...", "new": "..."}

Targets are cited the way lawyers cite them: a file (`art.15`, `s.13`, `sch.2`, `preamble`) followed by labels
(`s.8(1)(j)`, `sch.2(8)`) and, for unlabelled provisions, `/proviso`, `/proviso2`, `/explanation`. A block is the
amending text's own lines, one provision per line; `structure()` works out depth and formatting.
"""
import difflib
import json
import re
from pathlib import Path, PurePosixPath

SCHEMA = json.loads(Path(__file__).with_name("ops.schema.json").read_text(encoding="utf-8"))
OPS = {s["properties"]["op"]["const"]: s for s in SCHEMA["items"]["oneOf"]}  # the schema is the one list of ops
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
    if rest == "/heading":  # "in the marginal heading": the file's first line
        return path, 0, 1, -1
    every = nodes(files[path])
    hits = [n for n in every if n[0] == rest]
    if not hits and (tail := re.search(r"(/(?:explanation|proviso)\d*)+$", rest)):
        hits = unlabelled(every, rest[:tail.start()], re.findall(r"/[a-z]+\d*", tail[0]))
    if not hits and "/" not in rest:  # "clause (c)" of s.224, whose only clause (c) is in sub-section (2)
        inside = [n for n in every if n[0].endswith(rest)]
        hits = inside if len(inside) == 1 else []  # s.208 has (1)(c) and (2)(c): still not found
    if not hits:
        near = difflib.get_close_matches(rest, [n[0] for n in every], n=3, cutoff=0.4)
        raise EditError(f"{target}: not found in {path}" + (f"; nearest: {', '.join(m[1] + n for n in near)}" if near else ""))
    if len(hits) > 1:  # a Schedule that repeats its labels: (a) to (c) twice in the Constitution's Second
        raise EditError(f"{target}: {len(hits)} provisions in {path} have this ID; the target is ambiguous")
    return (path, *hits[0][1:])


def unlabelled(every, prefix, steps):
    """Provisos and Explanations that contract 2 nests differently from the drafting, found only when one fits.

    - "the Explanation" of s.18, printed after its last clause, nests under that clause: the only node of its kind
      anywhere inside the provision named is the one meant.
    - "in the second proviso, in Explanation I" (s.29A(c)): an Explanation printed after a proviso is its sibling
      here, so the last step alone is tried.
    - "in Explanation I ..., the proviso" (s.29A(j)): nothing nests under an Explanation, so its proviso is the
      first one after it, before the text leaves the Explanation's depth.
    """
    for scope in dict.fromkeys([prefix, re.sub(r"\(\w+\)$", "", prefix) or prefix]):  # then the provision around it:
        inside = [n for n in every if n[0].startswith(scope)]  # clause (b)'s Explanation, nested under (2)
        for tail in ("".join(steps), steps[-1]):
            found = [n for n in inside if n[0].endswith(tail)]
            if len(found) == 1:
                return found
    if len(steps) == 2 and steps[0].startswith("/explanation") and steps[1].startswith("/proviso"):
        owner = [n for n in inside if n[0].endswith(steps[0])]
        if len(owner) == 1:
            after = []
            for n in every[every.index(owner[0]) + 1:]:
                if n[3] < owner[0][3]:
                    break
                if re.search(r"/proviso\d*$", n[0]):
                    after.append(n)
            k = int(steps[1][len("/proviso"):] or 1)
            return after[k - 1:k]
    return []


def nearest(needle, hay):
    words, n = hay.split(), len(needle.split())
    spans = list(dict.fromkeys(" ".join(words[i:i + n]) for i in range(max(1, len(words) - n + 1))))
    best = difflib.get_close_matches(needle, spans, n=1, cutoff=0.5)
    return f"; nearest is {best[0]!r}" if best else ""


# --- Blocks: the amending text's lines, given their depth and our formatting -------------------------------

ROMAN = re.compile(r"^(?=[ivx])x{0,3}(ix|iv|v?i{0,3})$")


ROMANS = "i ii iii iv v vi vii viii ix x xi xii xiii xiv xv xvi xvii xviii xix xx".split()


def follows(label, last):
    if label.startswith(last):  # an inserted label: (ca) after (c), (4A) after (4)
        return True
    if label in ROMANS and last in ROMANS and ROMANS.index(label) == ROMANS.index(last) + 1:  # (iv), (v)
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
    entries = schedule and not any(m and m[2] for m in matches)  # "(15) Sashtra Seema Bal.": an entry, "15."
    for n, line in enumerate(lines):
        if labels[n]:
            label = labels[n]
            # "2." (a paragraph or entry) and "(2)" (its sub-paragraph) are different lists
            k = "para" if matches[n][2] else kind(label, stack, next((x for x in labels[n + 1:] if x), None))
            levels = [i for i, s in enumerate(stack) if s[0] == k]
            fits = [i for i in reversed(levels) if follows(label, stack[i][1])]
            depth = fits[0] if fits else levels[-1] if levels and label not in ("1", "a", "i", "A") else len(stack)
            stack = stack[:depth] + [(k, label)]
            if entries:
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


def section_file(block, beside):
    """(path, text) of a section an amendment inserts or substitutes, laid out as the parser lays out a section."""
    from constitution import HEAD_END, article, flat  # here, not at the top: constitution imports this module
    m = re.match(r"(\d+)-?([A-Z]*)\.\s?", block)  # "29A. ", "54-I. "
    if not m or not HEAD_END.search(block):
        raise EditError(f"a new section needs a number and a heading, \"29A. Heading.—\": {block[:60]!r}")
    head, lines, _ = article(block.split("\n"))
    kind = "article" if (file_id(beside) or "").startswith("art.") else "section"
    path = f"{PurePosixPath(beside).parent}/{kind}-{int(m[1]):03d}{m[2].lower()}.md".lstrip("./")
    return path, "\n".join([f"# {' '.join(flat(head).split())}", "", *(text for text, _ in lines)]) + "\n"


ORDINALS = "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split()


def schedule_file(block, beside):
    """(path, text) of a Schedule an amendment inserts or substitutes ("THE EIGHTH SCHEDULE (See section 43J) ...")."""
    from constitution import schedule  # here, not at the top: constitution imports this module
    m = re.match(rf"\W*((?:THE\s+)?({'|'.join(ORDINALS)})\s+SCHEDULE)\b\s*", block, re.I)
    if not m:
        raise EditError(f"a new Schedule needs its number, \"THE EIGHTH SCHEDULE\": {block[:60]!r}")
    lines, _ = schedule(block[m.end():].split("\n"))
    path = f"{PurePosixPath(beside).parent}/schedule-{ORDINALS.index(m[2].lower()) + 1}.md".lstrip("./")
    return path, "\n".join([f"# {' '.join(m[1].split())}", *(text for text, _ in lines)]) + "\n"


def chapter_files(block, beside):
    """{path: text} of a Chapter or Part an amendment inserts: its README and its sections, in a folder beside the
    Chapter's or Part's the section it follows is in ("CHAPTER III-A" after s.54 in part-ii/chapter-iii:
    part-ii/chapter-iii-a; "PART IA" after s.43 in part-i/chapter-x: part-ia)."""
    m = re.match(r"(CHAPTER|PART)\s+([IVXL]+(?:-?[A-Z])?)\s+(.*?)\s*\n?(?=\d+(?:-?[A-Z]+)?\.\s?)", block, re.S)
    if not m:
        raise EditError(f"a new Chapter or Part needs its number, title and sections: {block[:60]!r}")
    kind, number = m[1].lower(), m[2].lower()
    if kind == "chapter" and ("-" in number or number[-1] not in "ivxl"):  # "III-A" and "IIIA" are both
        number = re.sub(r"-?([a-z])$", r"-\1", number)  # chapter-iii-a, as the IBC prints them; "PART IA" is part-ia
    at = next((p for p in PurePosixPath(beside).parents if p.name.startswith(f"{kind}-")), PurePosixPath(beside))
    folder = f"{at.parent}/{kind}-{number}".lstrip("./")
    out = {f"{folder}/README.md": f"# {m[1]} {m[2]}\n\n{' '.join(m[3].split())}\n"}
    for section in re.split(r"\n(?=\d+(?:-?[A-Z]+)?\.\s?)", block[m.end():]):
        path, text = section_file(section, f"{folder}/README.md")
        out[path] = text
    return out


# --- The executor -----------------------------------------------------------------------------------------

def apply(files, ops):
    for op in ops:
        files = apply_one(files, op)
    return files


def check(op):
    """The op against engine/ops.schema.json: its fields, their types and the target's form. A field the schema
    doesn't give an op ("to" on INSERT_WORDS) is refused, not ignored."""
    spec = OPS.get(op.get("op"))
    if not spec or not set(spec["required"]) <= op.keys() <= spec["properties"].keys():
        raise EditError(f"{op}: expected one of {', '.join(OPS)} with fields {spec and spec['required']}")
    for k, v in op.items():
        p = spec["properties"][k]
        p = SCHEMA["$defs"][p["$ref"].split("/")[-1]] if "$ref" in p else p
        if (not isinstance(v, {"string": str, "boolean": bool}.get(p.get("type"), (str, bool)))
                or "enum" in p and v not in p["enum"] or isinstance(v, str) and len(v) < p.get("minLength", 0)
                or "pattern" in p and not re.fullmatch(p["pattern"], v)):
            raise EditError(f"{op}: {k} must be {p.get('description') or p.get('enum') or p.get('type')}")
    if op.get("every") and op.get("last"):
        raise EditError(f"{op}: every or last, not both")


def apply_one(files, op):
    check(op)
    name, target = op["op"], op["target"]
    path, first, end, depth = find(files, target)
    fid = file_id(path)
    if target.endswith("/heading") and name not in ("SUBSTITUTE_NODE", "SUBSTITUTE_WORDS", "INSERT_WORDS", "OMIT_WORDS"):
        raise EditError(f"{name} {target}: a heading can only be substituted or have its words changed")
    if first is None and name in ("INSERT_NODE", "SUBSTITUTE_NODE", "OMIT_NODE") and fid.startswith(("s.", "art.", "sch.")):
        rest = {p: t for p, t in files.items() if p != path or name == "INSERT_NODE"}  # a whole section, article or
        if name == "OMIT_NODE":  # Schedule is a file: added beside, replaced or deleted
            return rest
        if name == "INSERT_NODE" and op["block"].startswith(("CHAPTER", "PART")):
            new = chapter_files(op["block"], path)
        elif fid.startswith("sch."):  # the 2015 Act's Fourth to Seventh, one block
            new = dict(schedule_file(s, path) for s in re.split(
                rf"(?<!THE)\s(?=\W*(?:THE\s+)?(?:{'|'.join(map(str.upper, ORDINALS))})\s+SCHEDULE\b)", op["block"]))
        else:
            new = dict(section_file(s, path) for s in re.split(r"\n(?=\d+(?:-?[A-Z]+)?\.\s?)", op["block"]))  # 42, 42A
        have = {file_id(p) or p for p in rest}  # by ID, not path: a second s.54A in another folder is still s.54A
        if name == "INSERT_NODE" and (clash := sorted(p for p in new if (file_id(p) or p) in have)):
            raise EditError(f"{name} {target}: {', '.join(clash)} exists already")
        return {**rest, **new}
    lines = files[path].split("\n")
    if first is None:  # a whole file: everything after the heading
        first = 1 if lines[0].startswith("# ") else 0
        end = len(lines) - (lines[-1] == "")
    elif name in ("SUBSTITUTE_NODE", "OMIT_NODE", "INSERT_NODE") and re.search(r"/(?:proviso|explanation)\d*$", target):
        # a proviso's or an Explanation's own list ("(A) a scheduled bank; or") is printed after it at its depth
        # (contract 2 nests nothing under them): it goes with it. Only a list that starts there is its own: a
        # proviso to (a) printed before (b) leaves (b) alone
        item = end < len(lines) and ITEM.match(lines[end])
        label = item and len(item[1]) // 2 == depth and LABEL.match(item[2])
        while label and (label[1] or label[2]) in ("1", "a", "i", "A") and end < len(lines) \
                and (item := ITEM.match(lines[end])) and len(item[1]) // 2 == depth and LABEL.match(item[2]):
            end += 1
    region = "\n".join(lines[first:end])
    schedule = fid.startswith("sch.")

    if name in ("SUBSTITUTE_WORDS", "OMIT_WORDS", "INSERT_WORDS"):
        needle = op["old"] if name == "SUBSTITUTE_WORDS" else op["anchor"] if name == "INSERT_WORDS" else op["text"]
        to = rf"[^\n]*?{re.escape(op['to'])}" if op.get("to") else ""  # "the portion beginning with ... and ending with"
        # whole words: "payment" isn't in "repayment"; ", or hotels" starts where it starts
        words = re.compile((r"(?<!\w)" if re.match(r"\w", needle) else "") + re.escape(needle) + to
                           + (r"(?!\w)" if re.search(r"\w$", op.get("to") or needle) else ""))
        hits = list(words.finditer(region))
        if not hits:
            raise EditError(f"{name} {target}: {needle!r} not found{nearest(needle, region)}")
        if len(hits) > 1 and not op.get("every") and not op.get("last"):
            raise EditError(f"{name} {target}: {needle!r} occurs {len(hits)} times; name the provision it is in, "
                            "or say every, or last")
        gap = "" if name == "INSERT_WORDS" and op["text"][0] in ",;:.)" else " "  # after "shops": ", parks"
        new_words = (op["new"] if name == "SUBSTITUTE_WORDS" else "" if name == "OMIT_WORDS"
                     else f"{needle}{gap}{op['text']}" if op["position"] == "after" else f"{op['text']} {needle}")
        for hit in reversed(hits[-1:] if op.get("last") else hits):  # "occurring at the end": the last one only
            start = hit.start() - (name == "OMIT_WORDS" and hit.start() > 0 and region[hit.start() - 1] == " ")
            region = region[:start] + new_words + region[hit.end():]  # an omission takes the space before it
        new = region.split("\n")
    elif name == "SUBSTITUTE_NODE" and target.endswith("/heading"):  # a new marginal heading, same number
        new = [re.match(r"# \S+", lines[0])[0] + " " + " ".join(op["block"].split())]
    elif name == "OMIT_NODE":
        new = []
    elif name == "RENUMBER" and depth < 0:  # "section 9 ... renumbered as sub-section (1)": its opening words
        body = [line for line in lines[first:end] if line.strip()]  # become (1), and its list goes under them
        lead = [line for line in body if not ITEM.match(line)]
        if len(lead) != 1 or body[0] != lead[0]:
            raise EditError(f"{name} {target}: needs a section that opens with one paragraph, not a list")
        new = ["", f"- ({op['label']}) {lead[0].strip()}", *("  " + line for line in body[1:])]
    elif name == "RENUMBER":
        old = LABEL.match(ITEM.match(lines[first])[2])
        if not old:
            raise EditError(f"{name} {target}: has no label to renumber")
        new =[lines[first].replace(old[0], f"({op['label']}) " if old[1] else f"{op['label']}. ", 1), *lines[first + 1:end]]
    elif depth < 0 and name != "ADD_AT_END":
        raise EditError(f"{name} {target}: names a whole file; name a provision in it")
    elif name == "SUBSTITUTE_NODE":
        new = render(op["block"], depth, schedule)
    elif name == "INSERT_NODE":
        block = render(op["block"], depth, schedule)
        new = [*lines[first:end], *block] if op["position"] == "after" else [*block, *lines[first:end]]
    else:  # ADD_AT_END: the block becomes the target's last children (or the file's last provisions)
        new = [*lines[first:end], *render(op["block"], depth + 1, schedule)]
    return {**files, path: "\n".join([*lines[:first], *new, *lines[end:]])}
