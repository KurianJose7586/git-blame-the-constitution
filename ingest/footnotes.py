"""Footnotes of consolidated texts: what changed, by which instrument, from when (KICKOFF.md T15).

    parse("Subs. by the Constitution (Forty-second Amendment) Act, 1976, s.2, for “SOVEREIGN DEMOCRATIC "
          "REPUBLIC” (w.e.f. 3-1-1977).")
    == {"kind": "substituted", "instrument": "The Constitution (Forty-second Amendment) Act, 1976", "section": "2",
        "old": "SOVEREIGN DEMOCRATIC REPUBLIC", "wef": "1977-01-03", "pending": False, ...}

A footnote that names no change near its start ("See the Adaptation of Laws Order, 1950", a judgment, a remark)
gets kind None: it is a note, not an amendment. `parse_all` resolves "ibid." to the instrument before it.
"""
import re
from datetime import date

KINDS = {"subs": "substituted", "ins": "inserted", "rep": "repealed", "am": "amended"}
KIND = re.compile(r"\b(subs|substituted|ins|inserted|added|omitted|rep|repealed|re-?numbered|re-?lettered|am|amended)\b",
                  re.I)
QUOTED = re.compile(r"[“\"][^”\"]*[”\"]")
CONSTITUTION = re.compile(r"^(?:the\s+)?(Constitution\s*\(\s*[^)]*\)\s*Act\s*,?\s*\d{4})", re.I)
ORDER = re.compile(r"^(?:the\s+)?C\.\s*O\.\s*(\d+)")
NUMBERED = re.compile(r"^Act\s+(?:No\.\s*)?(\d+)\s+of\s+(\d{4})", re.I)
NOTIFICATION = re.compile(r"^(?:the\s+)?(?:notification|notifn\.)(?:\s+No\.)?\s*(G\.\s*S\.\s*R\.\s*[\w()]+|S\.\s*O\.\s*[\w()]+)?",
                          re.I)
NAMED = re.compile(r"^(?:the\s+)?([A-Z][^()]*?(?:\([^)]*\)[^()]*?)?\b(?:Act|Order|Ordinance|Regulations?|Rules)\b,?\s*\d{4})")
SECTION = re.compile(r"\bss?\.\s*(\d+[A-Z]?(?:\([\w]+\))*)")
WEF = re.compile(r"(?:w\.\s?e\.\s?f\.?|with effect from)\s*(\d{1,2})[-.](\d{1,2})[-.](\d{4})", re.I)  # "w.e.f 10-8-1975"
OLD = re.compile(r"\bfor\s+[“\"]\s*(.+?)\s*[”\"]")
PENDING = re.compile(r"not notif|to be notified|shall stand", re.I)
# "Ins. by the 38th Amendment ... and omitted by the 44th ...", "... and subsequently cl. (4) renumbered as ...":
# two changes in one note
CHANGE = r"(?:subs|ins|omitted|re-?numbered|re-?lettered|added)\b"
COMPOUND = re.compile(rf"\band\s+(?:further|subsequently|then)\s+(?=(?:\S+\s+){{0,2}}?{CHANGE})"
                      rf"|(?:\band\s+|This amendment was\s+|subsequently\s+)(?={CHANGE})", re.I)


def instrument_of(tail):
    if m := CONSTITUTION.match(tail):
        name = "The C" + re.sub(r"\(\s+", "(", " ".join(m[1].split()))[1:]
        name = re.sub(r"\((.*?) Amendment\)", lambda o: "(" + " ".join(  # "One-hundred and fourth"
            w if w == "and" else w[0].upper() + w[1:] for w in o[1].replace("-hundred", " Hundred").split()) + " Amendment)",
                      name)
    elif m := ORDER.match(tail):
        name = f"C.O. {m[1]}"
    elif m := NUMBERED.match(tail):
        name = f"Act {m[1]} of {m[2]}"
    elif m := NOTIFICATION.match(tail):
        name = "Notification" + (f" {' '.join(m[1].split())}" if m[1] else "")
    elif m := NAMED.match(tail):
        name = ("" if m[1].startswith("The ") else "The ") + " ".join(m[1].split())
    else:
        return None
    name = re.sub(r",(?= to\b)", "", name)  # "the Sixth Schedule, to the Constitution (Amendment) Act" is printed both ways
    return re.sub(r"\s*,\s*(\d{4})$", r", \1", name)  # "Act,1977", "Act , 2003"


def parse(text):
    text = " ".join(text.replace(chr(0xF02A), " ").split())  # the PDF's asterisk glyph
    text = re.sub(r"(?<!\S)((?:\w ){2,}\w)(?!\S)", lambda m: m[1].replace(" ", ""), text)  # "i n s ." -> "ins ."
    first = COMPOUND.split(text, 1)[0]  # of a compound note, the first change: its own date, words and section
    unquoted = QUOTED.sub("“”", first)
    kind = KIND.search(unquoted[:80])
    rest = unquoted[kind.end():] if kind else ""
    # The instrument follows "by", but not every "by": "subs. by articles 230 and 231 by the Constitution (...)".
    tails = [rest[m.end():] for m in re.finditer(r"\bby\s+", rest)] or [rest.lstrip(" .,")]
    tail, instrument = next(((t, i) for t in tails if (i := instrument_of(t))), (tails[0], None))
    section, wef = SECTION.search(tail), WEF.search(first)
    try:
        wef = wef and date(int(wef[3]), int(wef[2]), int(wef[1])).isoformat()
    except ValueError:  # "31-11-1956": no such day
        wef = None
    old = (OLD.search(first)  # what a change replaced: "for “X”", "The words “X” omitted", "Cl. (a) re-lettered"
           or re.search(r"[“\"]([^”\"]+)[”\"]\s+(?:\S+\s+){0,2}?omitted\b", first)
           or re.search(r"(\(\w+\))\s+(?:shall stand\s+)?re-?(?:lettered|numbered)\b", first))
    k = kind[1].lower().replace("-", "") if kind else None
    return {
        "kind": KINDS.get(k, k),
        "instrument": instrument,
        "ibid": bool(kind) and not instrument and bool(re.search(r"\bibid\b", tail[:40])),
        "section": section[1] if section else None,
        "old": old[1] if old else None,
        "wef": wef,
        "retrospective": "retrospective" in first,
        "pending": bool(PENDING.search(first)),
        "text": text,
    }


def parse_all(texts):
    """parse() each footnote in document order, resolving "ibid." to the instrument before it. After a compound
    note ("Ins. by the 88th ... and further subs. by the 101st ..."), that is its later instrument, unless the
    ibid. note is compound too: "Subs. by s. 50, ibid., ... and further subs. by s. 38, ibid." follows its pattern."""
    out, first, last = [], None, None
    for text in texts:
        r = parse(text)
        if r["ibid"]:
            r["instrument"] = first if COMPOUND.search(r["text"]) else last
        named = [i for t in re.split(r"\bby\s+", QUOTED.sub("“”", r["text"]))[1:] if (i := instrument_of(t))]
        first = r["instrument"] or first
        last = named[-1] if named else first
        out.append(r)
    return out
