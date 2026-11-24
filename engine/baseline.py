"""Regex baseline (KICKOFF.md T16): the text of one amending provision -> edit operations, for formulaic drafting.

    ops, misses = baseline('In article 15 of the Constitution, after clause (4), the following clause shall be '
                           'inserted, namely:—\n"(5) Nothing in this article ...".')

`misses` lists the instructions no rule understood; the baseline never guesses.
"""
import re
import string

from ops import ORDINALS, ROMAN, ROMANS

Q = "[\"“”'‘’]"
OF_ACT = r"(?:\s+of\s+the\s+(?:principal Act|[A-Z][\w ()]*?,\s*\d{4}(?:\s*\([^)]*\))*))?"  # "of the principal Act"
UNLABELLED = (r"(?:the\s+)?(?:(?P<nth>first|second|third|fourth)\s+)?(?P<unlabelled>proviso|Explanation)s?"
              r"(?:\s+(?P<numeral>I{1,3}|IV|[1-4])\b)?"  # "Explanation II" is the second Explanation
              r"(?:\s+to\s+(?:sub-section|clause|sub-clause)\s*\((?P<of>\w+)\))?")  # "the Explanation to sub-section (2)"
NODE = (r"(?:(?P<kind>sub-section|sub-clause|clause|article|section|serial number|S\.\s?No\.|item|entry)\s*"
        r"(?:\((?P<label>[0-9A-Za-z]+)\)|(?<=[a-z.] )(?P<bare>[0-9]+[A-Z]*))"  # "clause (4)", "section 29", "item 3"
        r"(?:\s+and\s+the\s+entr(?:y|ies)\s+relating\s+thereto)?(?:\s+as\s+so\s+re-?(?:numbered|lettered))?|"
        + UNLABELLED + ")" + OF_ACT)
RENUMBERED = re.compile(r"\b(?:sub-section|sub-clause|clause)\s*\((?P<old>\w+)\)\s+shall\s+be\s+re-?(?:numbered|lettered)"
                        r"\s+as\s+(?:sub-section|sub-clause|clause)\s*\((?P<new>\w+)\)", re.I)  # "(a) ... as clause (aa)"
WHOLE_RENUMBERED = re.compile(r"\bsection\s+(?P<section>\d+[A-Z]*)(?:\s+of\s+the\s+principal\s+Act)?\s+shall\s+be\s+"
                              r"re-?numbered\s+as\s+(?:sub-section\s*|section\s*\d+[A-Z]*)\((?P<new>\w+)\)", re.I)
# "Section 9 ... shall be renumbered as sub-section (1) thereof": its text becomes the section's sub-section (1)
WORDS = r"(?:the\s+)?(?:words?|figures?|letters?|brackets?)(?:(?:,|\s+and)\s+(?:words?|figures?|letters?|brackets?))*,?"
PLACES = (r"(?:\s*(?:(?P<every>(?:at\s+(?:both|all)\s+the\s+places\s+where|wherever)\s+(?:they|it)\s+occurs?"
          r"|occurring\s+at\s+(?:both|all)\s+the\s+places)"
          r"|(?P<last>occurring\s+at\s+the\s+end)),?)?")
FILE = [(r"\bthe Preamble\b", lambda m: "preamble"), (r"\b(?i:article)\s+(\d+[A-Z]*)", lambda m: f"art.{m[1]}"),
        (r"\b(?i:section)\s+(\d+)-?([A-Z]*)", lambda m: f"s.{m[1]}{m[2]}"),  # "section 54-I" is s.54I
        (rf"\b((?i:{'|'.join(ORDINALS)}))\s+Schedule\b", lambda m: f"sch.{ORDINALS.index(m[1].lower()) + 1}")]
LOCATION = re.compile(r"(?:\bin|\boccurring\s+after)\s+"  # "in clause (a)"; "the Explanation occurring after clause (j)"
                      r"(?:(?:sub-section|sub-clause|clause)\s*\((?P<label>[0-9A-Za-z]+)\)"
                      r"|(?:serial number|S\.\s?No\.|item)\s*\(?(?P<bare>[0-9A-Za-z]+)\)?"
                      r"|the (?P<heading>marginal heading)|" + UNLABELLED + r")"
                      r"(?!\s+and\s+\()", re.I)  # "in clauses (a) and (b)" stays where it is: one rule for both
NUMBERED = re.compile(r"\bthe Explanation\b.*?\bshall be (?:re-?)?numbered as Explanation\s+(?P<numeral>[IVX]+|\d+)\b", re.I)
RULES = [  # (op, pattern); word rules quote inline, node rules take the block that follows the instruction
    ("SUBSTITUTE_WORDS", rf"for {WORDS}\s*{Q}+(?P<old>.+?){Q}+,?{PLACES}\s*{WORDS}\s*{Q}+(?P<new>.+?){Q}+,?\s*shall be substituted"),
    ("INSERT_WORDS", rf"(?P<position>after|before) {WORDS}\s*{Q}+(?P<anchor>.+?){Q}+,?{PLACES}\s*{WORDS}\s*{Q}+(?P<text>.+?){Q}+,?\s*shall be inserted"),
    ("OMIT_WORDS", rf"{WORDS}\s*{Q}+(?P<text>.+?){Q}+,?{PLACES}\s*shall be omitted"),
    ("SUBSTITUTE_NODE", rf"\bfor\s+{NODE},?\s*the following\b.*?shall be substituted"),
    ("INSERT_NODE", rf"\b(?P<position>after|before)\s+{NODE},?\s*the following\b.*?shall be (?:inserted|added)"),
    ("OMIT_NODE", rf"(?:^|,\s*)(?:\(\w+\)\s+)?{NODE}\s+shall be omitted"),
    ("ADD_AT_END", r"\bthe following\b.*?shall be (?:added|inserted)"),  # with no "after" or "before": at the end
]
CHAPTER = re.compile(r"\bafter\s+(?:Chapter|Part)\s+[IVXL]+[A-Z-]*" + OF_ACT + r",?\s+the following (?:Chapter|Part) shall be "
                     r"inserted", re.I)
SCHEDULE = re.compile(rf"\b(?:(?P<position>after|before)|for)\s+the\s+(?P<nth>{'|'.join(ORDINALS)})\s+Schedule\b"
                      r"(?:\s+to\s+the\s+principal\s+Act)?,?\s+the following (?:new\s+)?Schedules?\s+shall\s+be\s+"
                      r"(?:inserted|substituted)", re.I)
SCHEDULE_OMITTED = re.compile(rf"\bthe\s+(?P<nth>{'|'.join(ORDINALS)})\s+Schedule\b(?:\s+to\s+the\s+principal\s+Act)?\s+"
                              r"shall\s+be\s+omitted", re.I)
PORTION = re.compile(rf"\bfor the portion beginning with\s+{Q}+(?P<old>.+?){Q}+\s+and ending with\s+{Q}+(?P<to>.+?){Q}+,?\s+"
                     r"the following shall be substituted", re.I)
LABELS = r"\(\w+\)(?:,?\s*(?:and\s+|to\s+)?\(\w+\))+"  # "(7) and (8)", "(3), (4), (5) and (6)", "(11) to (14)"
PAIR = re.compile(rf"\bfor\s+(?:sub-sections|clauses|sub-clauses)\s+(?P<labels>{LABELS}),?\s*the following\b.*?"
                  r"shall be substituted", re.I)
OMIT_MANY = re.compile(rf"\b(?:(?P<kind>sub-sections|clauses|sub-clauses)\s+(?P<labels>{LABELS})"
                       r"|sections\s+(?P<numbers>\d+[A-Z]*(?:,?\s*(?:and\s+)?\d+[A-Z]*)+)"  # "sections 38, 39 and 42"
                       r")(?:\s+of the principal Act)?\s+shall be omitted", re.I)
HEADING = re.compile(rf"\bfor the marginal heading,\s+(?:the following marginal heading|the marginal heading\s+{Q}(?P<new>.+?){Q})"
                     r"\s+shall be substituted", re.I)
NTH = {"": "", "first": "", "i": "", "1": "", "second": "2", "ii": "2", "2": "2", "third": "3", "iii": "3", "3": "3",
       "fourth": "4", "iv": "4", "4": "4"}  # "the second proviso", "Explanation II"


DOUBLE, SINGLE = "(?:[\"”]|’’)", "[’']"  # a double close is sometimes typeset as two single ones: "’’."
CLOSE = {'"': DOUBLE, "“": DOUBLE, "”": DOUBLE, "'": SINGLE, "‘": SINGLE, "’": SINGLE}  # ' closes only with '


def split(text):
    """Instruction lines, each with the quoted block that follows it (or None). A block opened with a single quote
    holds terms in double quotes ('(2A) "base resolution plan" means'), so only a single quote closes it."""
    items, block, end, curly = [], None, None, False
    for line in (l.strip() for l in text.split("\n")):
        if not line:
            continue
        if block is None and re.match(Q, line) and items:  # a quoted block opens; "‘‘" is a double quote typeset as two
            two, curly = line.startswith(("‘‘", "''")), line[0] == "“"
            block, end = [line[1 + two:]], re.compile(rf"{DOUBLE if two else CLOSE[line[0]]}\s*[.;,]?(\s*and)?\s*$")
        elif block is not None:
            block.append(line)
        else:
            items.append([line, None])
            continue
        inner = "\n".join(block)
        closes = inner.count("”") + inner.count("’’")  # "’’" is a closing double typeset as two singles
        if end.search(block[-1]) and (not curly or closes > inner.count("“") + inner.count("‘‘")):  # ... and closes
            block[-1] = end.sub("", block[-1])
            items[-1][1], block = "\n".join(block), None
    if block is not None:  # never closed: the instruction it belongs to is a miss
        items[-1][0] = f"{items[-1][0]} [quoted block not closed]"
        items[-1][1] = None
    return items


def suffix(g):
    """A target's last step: "(4)", or "/proviso2" for "the second proviso"."""
    if g.get("unlabelled"):
        of = f"({g['of']})" if g.get("of") else ""
        return f"{of}/{g['unlabelled'].lower()}{NTH[(g.get('numeral') or g.get('nth') or '').lower()]}"
    if g.get("heading"):
        return "/heading"
    return f"({g.get('label') or g['bare']})"


SEQUENCES = [ROMANS, [str(n) for n in range(1, 500)], list(string.ascii_lowercase), list(string.ascii_uppercase)]


def labels(text):
    """The labels a list names: "(3), (4) and (6)"; "(11) to (14)" and "(a) to (d)" are every label between. None
    for a range it can't count ("(2A) to (2D)"), so the instruction is a miss, not half applied."""
    out = []
    for a, b in re.findall(r"\((\w+)\)(?:\s+to\s+\((\w+)\))?", text):
        seq = next((s for s in SEQUENCES if a in s and b in s and s.index(a) < s.index(b)), None) if b else [a]
        if seq is None:
            return None
        out += seq[seq.index(a):seq.index(b) + 1] if b else seq
    return out


def list_kind(line, last=None):
    """The kind of the label an instruction starts with, "(a) in sub-section (1),—": siblings share a kind. (i)
    after (h), the last letter seen, is a letter."""
    m = re.match(r"\((\w+)\)\s", line)
    if not m:
        return None
    label = m[1]
    return ("num" if label[0].isdigit()
            else "Roman" if ROMAN.match(label.lower()) and label.isupper()  # "(I) in clause (j)" holds "(A)"
            else "upper" if label.isupper()
            else "roman" if ROMAN.match(label) and not (last and ord(label[0]) == ord(last) + 1 and len(label) == 1)
            else "alpha")


def baseline(text):
    ops, misses, file, context, last = [], [], None, [], None  # context: [(list kind, location)] of the lines above
    for line, block in split(text):
        unquoted = re.sub(r"[“\"][^”\"]*[”\"]|‘‘.*?’’", "", line)  # "[See section 11 (14)]", "in clause (a)" quoted
        start = (m.start() if (m := re.search(r"\b[Ii]n\s", unquoted)) else 0)
        named = [(m.start(), make(m)) for pattern, make in FILE if (m := re.compile(pattern).search(unquoted, start))]
        file = file or min(named, default=(0, None))[1]
        kind = list_kind(line, last)
        if kind:  # a sibling replaces the context of the one before it
            context = context[:next((i for i, (k, _) in enumerate(context) if k == kind), len(context))]
            last = re.match(r"\((\w+)\)", line)[1] if kind == "alpha" else last
        loc = "".join(suffix(m.groupdict()) for m in LOCATION.finditer(unquoted))
        where = f"{file}{''.join(loc for _, loc in context)}{loc}"
        found = False
        if block is not None and CHAPTER.search(line) and (m := re.search(r"(\d+)[A-Z]+\.\s", block)):
            ops.append({"op": "INSERT_NODE", "target": f"s.{m[1]}", "position": "after", "block": block})
            continue  # a new Chapter goes after the section its first section follows: 54A after s.54
        if block is not None and (m := SCHEDULE.search(line)):  # a whole Schedule: a file of its own
            target = f"sch.{ORDINALS.index(m['nth'].lower()) + 1}"
            ops.append({"op": "INSERT_NODE", "target": target, "position": m["position"].lower(), "block": block}
                       if m["position"] else {"op": "SUBSTITUTE_NODE", "target": target, "block": block})
            continue
        if m := SCHEDULE_OMITTED.search(unquoted):
            ops.append({"op": "OMIT_NODE", "target": f"sch.{ORDINALS.index(m['nth'].lower()) + 1}"})
            continue
        if block is not None and (m := PORTION.search(line)):  # "in the long line, for the portion beginning with"
            ops.append({"op": "SUBSTITUTE_WORDS", "target": where, "old": m["old"].strip(), "to": m["to"].strip(),
                        "new": " ".join(block.split())})
            continue
        if block is not None and (m := PAIR.search(line)) and labels(m["labels"]):  # "for sub-sections (7) and
            first, *rest = labels(m["labels"])  # (8)": all but the first go, and the first takes the whole block
            ops += [{"op": "OMIT_NODE", "target": f"{where}({label})"} for label in reversed(rest)]
            ops.append({"op": "SUBSTITUTE_NODE", "target": f"{where}({first})", "block": block})
            continue
        if (m := OMIT_MANY.search(unquoted)) and (m["numbers"] or labels(m["labels"])):  # "sections 38, 39 and 42"
            ops += ([{"op": "OMIT_NODE", "target": f"s.{n}"} for n in re.findall(r"\d+[A-Z]*", m["numbers"])]
                    if m["numbers"] else
                    [{"op": "OMIT_NODE", "target": f"{where}({label})"} for label in labels(m["labels"])])
            continue
        if (m := HEADING.search(line)) and (m["new"] or block):  # a new marginal heading
            ops.append({"op": "SUBSTITUTE_NODE", "target": f"{file}/heading", "block": m["new"] or block})
            continue
        renumbered = [{"op": "RENUMBER", "target": f"{where}({m['old']})", "label": m["new"]}
                      for m in RENUMBERED.finditer(unquoted)]  # first, so "before clause (2B)" finds it
        renumbered += [{"op": "RENUMBER", "target": f"s.{m['section']}", "label": m["new"]}
                       for m in WHOLE_RENUMBERED.finditer(unquoted)]
        renumbered += [{"op": "INSERT_WORDS", "target": re.sub(r"(/explanation\d*)?$", "/explanation", where, count=1),
                        "position": "after", "anchor": "Explanation", "text": m["numeral"]}
                       for m in NUMBERED.finditer(unquoted)]  # "the Explanation shall be numbered as Explanation I"
        ops += renumbered
        for op, pattern in RULES:
            for m in re.finditer(pattern, line, re.I):
                if op.endswith(("_NODE", "AT_END")) and op != "OMIT_NODE" and block is None:
                    continue
                g = {k: v for k, v in m.groupdict().items() if v is not None}
                node = {k: g.pop(k) for k in ("kind", "label", "bare", "nth", "unlabelled", "numeral", "of") if k in g}
                for flag in ("every", "last"):  # "at both the places where they occur", "occurring at the end"
                    if g.pop(flag, None):
                        g[flag] = True
                if node.get("kind", "").lower() in ("section", "article"):  # a whole section: a file of its own
                    number = node.get("bare") or node.get("label")
                    target = f"{'s' if node['kind'].lower() == 'section' else 'art'}.{number}"
                else:
                    target = where + (suffix(node) if op.endswith("_NODE") else "")
                ops.append({"op": op, "target": target,  # quoted words without the spaces inside the quotes
                            **{k: v.lower() if k == "position" else v.strip() if isinstance(v, str) else v
                               for k, v in g.items()},
                            **({"block": block} if op.endswith(("_NODE", "AT_END")) and op != "OMIT_NODE" else {})})
                found = True
            if found:
                break
        if not found and not renumbered:
            if not re.search(r"shall be|namely", line, re.I) and re.search(r"(?:^|\)\s)in\b|[—:-]$", line, re.I):
                context.append((kind, loc))  # context only: "In section 13 of the principal Act,—"
            else:
                misses.append(line)
    return ops, misses
