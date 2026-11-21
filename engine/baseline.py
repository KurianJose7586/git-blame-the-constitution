"""Regex baseline (KICKOFF.md T16): the text of one amending provision -> edit operations, for formulaic drafting.

    ops, misses = baseline('In article 15 of the Constitution, after clause (4), the following clause shall be '
                           'inserted, namely:—\n"(5) Nothing in this article ...".')

`misses` lists the instructions no rule understood; the baseline never guesses.
"""
import re

Q = "[\"“”'‘’]"
END_QUOTE = re.compile(rf"{Q}\s*[.;,]?(\s*and)?\s*$")
NODE = r"(?:sub-section|sub-clause|clause|article|serial number|S\.\s?No\.)\s*\(?([0-9A-Za-z]+)\)?(?:\s+and\s+the\s+entr(?:y|ies)\s+relating\s+thereto)?"
FILE = [(r"\bthe Preamble\b", lambda m: "preamble"), (r"\barticle\s+(\d+[A-Z]*)", lambda m: f"art.{m[1]}"),
        (r"\bsection\s+(\d+[A-Z]*)", lambda m: f"s.{m[1]}"),
        (r"\b(First|Second|Third|Fourth|Fifth|Sixth)\s+Schedule\b",
         lambda m: f"sch.{['first', 'second', 'third', 'fourth', 'fifth', 'sixth'].index(m[1].lower()) + 1}")]
LOCATION = re.compile(r"\bin\s+(?:sub-section|sub-clause|clause|serial number|S\.\s?No\.)\s*\(?([0-9A-Za-z]+)\)?", re.I)
RULES = [  # (op, pattern); word rules quote inline, node rules take the block that follows the instruction
    ("SUBSTITUTE_WORDS", rf"for the words?,?\s*{Q}(?P<old>.+?){Q},?\s*the words?,?\s*{Q}(?P<new>.+?){Q},?\s*shall be substituted"),
    ("INSERT_WORDS", rf"(?P<position>after|before) the words?,?\s*{Q}(?P<anchor>.+?){Q},?\s*the words?,?\s*{Q}(?P<text>.+?){Q},?\s*shall be inserted"),
    ("OMIT_WORDS", rf"(?:the\s+)?words?,?\s*{Q}(?P<text>.+?){Q},?\s*shall be omitted"),
    ("SUBSTITUTE_NODE", rf"\bfor\s+{NODE},?\s+the following\b.*?shall be substituted"),
    ("INSERT_NODE", rf"\b(?P<position>after|before)\s+{NODE},?\s+the following\b.*?shall be (?:inserted|added)"),
    ("OMIT_NODE", rf"^(?:\(\w+\)\s+)?{NODE}\s+shall be omitted"),
    ("ADD_AT_END", r"\bthe following\b.*?shall be added"),
]


def split(text):
    """Instruction lines, each with the quoted block that follows it (or None)."""
    items, block = [], None
    for line in (l.strip() for l in text.split("\n")):
        if not line:
            continue
        if block is None and re.match(Q, line) and items:  # a quoted block opens
            block = [line[1:]]
        elif block is not None:
            block.append(line)
        else:
            items.append([line, None])
            continue
        if END_QUOTE.search(block[-1]):  # ... and closes
            block[-1] = END_QUOTE.sub("", block[-1])
            items[-1][1], block = "\n".join(block), None
    return items


def baseline(text):
    ops, misses, file, where = [], [], None, ""
    for line, block in split(text):
        for pattern, make in FILE:
            if not file and (m := re.search(pattern, line)):
                file = make(m)
        loc = "".join(f"({x})" for x in LOCATION.findall(line))
        found = False
        for op, pattern in RULES:
            for m in re.finditer(pattern, line, re.I):
                if op.endswith(("_NODE", "AT_END")) and op != "OMIT_NODE" and block is None:
                    continue
                g = {k: v for k, v in m.groupdict().items() if v is not None}
                node = next((x for x in m.groups() if x and x not in g.values()), None)
                target = f"{file}{where}{loc}" + (f"({node})" if op.endswith("_NODE") else "")
                ops.append({"op": op, "target": target, **{k: v.lower() if k == "position" else v for k, v in g.items()},
                            **({"block": block} if op.endswith(("_NODE", "AT_END")) and op != "OMIT_NODE" else {})})
                found = True
            if found:
                break
        if not found:
            if not re.search(r"shall be|namely", line, re.I):  # context only: "In section 13 of the principal Act,—"
                where += loc
            else:
                misses.append(line)
    return ops, misses
