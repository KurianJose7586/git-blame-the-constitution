"""Regex baseline (KICKOFF.md T16): the text of one amending provision -> edit operations, for formulaic drafting.

    ops, misses = baseline('In article 15 of the Constitution, after clause (4), the following clause shall be '
                           'inserted, namely:—\n"(5) Nothing in this article ...".')

`misses` lists the instructions no rule understood; the baseline never guesses.
"""
import re

Q = "[\"“”'‘’]"
END_QUOTE = re.compile(rf"{Q}\s*[.;,]?(\s*and)?\s*$")
OF_ACT = r"(?:\s+of\s+the\s+(?:principal Act|[A-Z][\w ()]*?,\s*\d{4}(?:\s*\([^)]*\))*))?"  # "of the principal Act"
UNLABELLED = r"(?:the\s+)?(?:(?P<nth>first|second|third|fourth)\s+)?(?P<unlabelled>proviso|Explanation)s?"
NODE = (r"(?:(?P<kind>sub-section|sub-clause|clause|article|section|serial number|S\.\s?No\.|item|entry)\s*"
        r"(?:\((?P<label>[0-9A-Za-z]+)\)|(?<=[a-z.] )(?P<bare>[0-9]+[A-Z]*))"  # "clause (4)", "section 29", "item 3"
        r"(?:\s+and\s+the\s+entr(?:y|ies)\s+relating\s+thereto)?|" + UNLABELLED + ")" + OF_ACT)
WORDS = r"(?:the\s+)?(?:words?|figures?|letters?|brackets?)(?:(?:,|\s+and)\s+(?:words?|figures?|letters?|brackets?))*,?"
PLACES = r"(?:\s*(?P<every>(?:at\s+(?:both|all)\s+the\s+places\s+where|wherever)\s+(?:they|it)\s+occurs?),?)?"
ORDINALS = "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split()
FILE = [(r"\bthe Preamble\b", lambda m: "preamble"), (r"\barticle\s+(\d+[A-Z]*)", lambda m: f"art.{m[1]}"),
        (r"\bsection\s+(\d+[A-Z]*)", lambda m: f"s.{m[1]}"),
        (rf"\b((?i:{'|'.join(ORDINALS)}))\s+Schedule\b", lambda m: f"sch.{ORDINALS.index(m[1].lower()) + 1}")]
LOCATION = re.compile(r"\bin\s+(?:(?:sub-section|sub-clause|clause)\s*\((?P<label>[0-9A-Za-z]+)\)"
                      r"|(?:serial number|S\.\s?No\.|item)\s*\(?(?P<bare>[0-9A-Za-z]+)\)?"
                      r"|the (?P<heading>marginal heading)|" + UNLABELLED + r")"
                      r"(?!\s+and\s+\()", re.I)  # "in clauses (a) and (b)" stays where it is: one rule for both
RULES = [  # (op, pattern); word rules quote inline, node rules take the block that follows the instruction
    ("SUBSTITUTE_WORDS", rf"for {WORDS}\s*{Q}(?P<old>.+?){Q},?{PLACES}\s*{WORDS}\s*{Q}(?P<new>.+?){Q},?\s*shall be substituted"),
    ("INSERT_WORDS", rf"(?P<position>after|before) {WORDS}\s*{Q}(?P<anchor>.+?){Q},?{PLACES}\s*{WORDS}\s*{Q}(?P<text>.+?){Q},?\s*shall be inserted"),
    ("OMIT_WORDS", rf"{WORDS}\s*{Q}(?P<text>.+?){Q},?{PLACES}\s*shall be omitted"),
    ("SUBSTITUTE_NODE", rf"\bfor\s+{NODE},?\s+the following\b.*?shall be substituted"),
    ("INSERT_NODE", rf"\b(?P<position>after|before)\s+{NODE},?\s+the following\b.*?shall be (?:inserted|added)"),
    ("OMIT_NODE", rf"(?:^|,\s*)(?:\(\w+\)\s+)?{NODE}\s+shall be omitted"),
    ("ADD_AT_END", r"\bthe following\b.*?shall be (?:added|inserted)"),  # with no "after" or "before": at the end
]
CHAPTER = re.compile(r"\bafter\s+Chapter\s+[IVXL]+[A-Z-]*" + OF_ACT + r",?\s+the following Chapter shall be inserted", re.I)
PAIR = re.compile(r"\bfor\s+(?:sub-sections|clauses|sub-clauses)\s+\((?P<first>\w+)\)\s+and\s+\((?P<second>\w+)\),?"
                  r"\s+the following\b.*?shall be substituted", re.I)
NTH = {None: "", "first": "", "second": "2", "third": "3", "fourth": "4"}


CLOSE = {'"': '"”', "“": '”"', "'": "'’", "‘": "’'", "”": '”"', "’": "’'"}  # a block opened with ' closes with '


def split(text):
    """Instruction lines, each with the quoted block that follows it (or None). A block opened with a single quote
    holds terms in double quotes ('(2A) "base resolution plan" means'), so only a single quote closes it."""
    items, block, end = [], None, END_QUOTE
    for line in (l.strip() for l in text.split("\n")):
        if not line:
            continue
        if block is None and re.match(Q, line) and items:  # a quoted block opens
            block, end = [line[1:]], re.compile(rf"[{CLOSE[line[0]]}]\s*[.;,]?(\s*and)?\s*$")
        elif block is not None:
            block.append(line)
        else:
            items.append([line, None])
            continue
        if end.search(block[-1]):  # ... and closes
            block[-1] = end.sub("", block[-1])
            items[-1][1], block = "\n".join(block), None
    return items


def suffix(g):
    """A target's last step: "(4)", or "/proviso2" for "the second proviso"."""
    if g.get("unlabelled"):
        return f"/{g['unlabelled'].lower()}{NTH[(g.get('nth') or '').lower() or None]}"
    if g.get("heading"):
        return "/heading"
    return f"({g.get('label') or g['bare']})"


def list_kind(line):
    """The kind of the label an instruction starts with, "(a) in sub-section (1),—": siblings share a kind."""
    m = re.match(r"\((\w+)\)\s", line)
    if not m:
        return None
    label = m[1]
    return ("num" if label[0].isdigit() else "upper" if label.isupper()
            else "roman" if re.fullmatch(r"(?=[ivx])x{0,3}(ix|iv|v?i{0,3})", label) else "alpha")


def baseline(text):
    ops, misses, file, context = [], [], None, []  # context: [(list kind, location)] of the lines above
    for line, block in split(text):
        for pattern, make in FILE:
            if not file and (m := re.search(pattern, line)):
                file = make(m)
        kind = list_kind(line)
        if kind:  # a sibling replaces the context of the one before it
            context = context[:next((i for i, (k, _) in enumerate(context) if k == kind), len(context))]
        unquoted = re.sub(r"[“\"][^”\"]*[”\"]", "", line)  # "in clause (a)" inside quoted words isn't a location
        loc = "".join(suffix(m.groupdict()) for m in LOCATION.finditer(unquoted))
        where = f"{file}{''.join(loc for _, loc in context)}{loc}"
        found = False
        if block is not None and CHAPTER.search(line) and (m := re.search(r"(\d+)[A-Z]+\.\s", block)):
            ops.append({"op": "INSERT_NODE", "target": f"s.{m[1]}", "position": "after", "block": block})
            continue  # a new Chapter goes after the section its first section follows: 54A after s.54
        if block is not None and (m := PAIR.search(line)):  # "for sub-sections (7) and (8)": the second goes, the
            ops += [{"op": "OMIT_NODE", "target": f"{where}({m['second']})"},  # first takes the whole block
                    {"op": "SUBSTITUTE_NODE", "target": f"{where}({m['first']})", "block": block}]
            continue
        for op, pattern in RULES:
            for m in re.finditer(pattern, line, re.I):
                if op.endswith(("_NODE", "AT_END")) and op != "OMIT_NODE" and block is None:
                    continue
                g = {k: v for k, v in m.groupdict().items() if v is not None}
                node = {k: g.pop(k) for k in ("kind", "label", "bare", "nth", "unlabelled") if k in g}
                if g.pop("every", None):  # "at both the places where they occur"
                    g["every"] = True
                if node.get("kind", "").lower() in ("section", "article"):  # a whole section: a file of its own
                    number = node.get("bare") or node.get("label")
                    target = f"{'s' if node['kind'].lower() == 'section' else 'art'}.{number}"
                else:
                    target = where + (suffix(node) if op.endswith("_NODE") else "")
                ops.append({"op": op, "target": target, **{k: v.lower() if k == "position" else v for k, v in g.items()},
                            **({"block": block} if op.endswith(("_NODE", "AT_END")) and op != "OMIT_NODE" else {})})
                found = True
            if found:
                break
        if not found:
            if not re.search(r"shall be|namely", line, re.I):  # context only: "In section 13 of the principal Act,—"
                context.append((kind, loc))
            else:
                misses.append(line)
    return ops, misses
