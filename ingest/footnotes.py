"""Footnotes of consolidated texts: what changed, by which instrument, from when (KICKOFF.md T15).

    parse("Subs. by the Constitution (Forty-second Amendment) Act, 1976, s.2, for “SOVEREIGN DEMOCRATIC "
          "REPUBLIC” (w.e.f. 3-1-1977).")
    == {"kind": "substituted", "instrument": "The Constitution (Forty-second Amendment) Act, 1976", "section": "2",
        "old": "SOVEREIGN DEMOCRATIC REPUBLIC", "wef": "1977-01-03", "pending": False, ...}

A footnote that names no change near its start ("See the Adaptation of Laws Order, 1950", a judgment, a remark)
gets kind None: it is a note, not an amendment. `parse_all` resolves "ibid." to the instrument before it.
"""
import re

KINDS = {"subs": "substituted", "substituted": "substituted", "ins": "inserted", "inserted": "inserted",
         "added": "added", "omitted": "omitted", "rep": "repealed", "repealed": "repealed",
         "renumbered": "renumbered", "relettered": "relettered", "am": "amended", "amended": "amended"}
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
WEF = re.compile(r"(?:w\.\s?e\.\s?f\.|with effect from)\s*(\d{1,2})[-.](\d{1,2})[-.](\d{4})", re.I)
OLD = re.compile(r"\bfor\s+[“\"]\s*(.+?)\s*[”\"]")
PENDING = re.compile(r"not notif|to be notified|shall stand", re.I)


def parse(text):
    text = " ".join(text.replace("", " ").split())
    text = re.sub(r"(?<!\S)((?:\w ){2,}\w)(?!\S)", lambda m: m[1].replace(" ", ""), text)  # "i n s ." -> "ins ."
    unquoted = QUOTED.sub("“”", text)
    kind = KIND.search(unquoted[:80])
    rest = unquoted[kind.end():] if kind else ""
    tail = (m[1] if (m := re.search(r"\bby\s+(.*)", rest)) else rest.lstrip(" .,"))
    instrument = None
    if m := CONSTITUTION.match(tail):
        instrument = "The C" + re.sub(r"\(\s+", "(", " ".join(m[1].split()))[1:].replace(" Act ,", " Act,")
    elif m := ORDER.match(tail):
        instrument = f"C.O. {m[1]}"
    elif m := NUMBERED.match(tail):
        instrument = f"Act {m[1]} of {m[2]}"
    elif m := NOTIFICATION.match(tail):
        instrument = "Notification" + (f" {' '.join(m[1].split())}" if m[1] else "")
    elif m := NAMED.match(tail):
        instrument = ("" if m[1].startswith("The ") else "The ") + " ".join(m[1].split())
    section, wef, old = SECTION.search(tail), WEF.search(text), OLD.search(text)
    return {
        "kind": KINDS[kind[1].lower().replace("-", "")] if kind else None,
        "instrument": instrument,
        "ibid": bool(kind) and not instrument and bool(re.search(r"\bibid\b", tail[:40])),
        "section": section[1] if section else None,
        "old": old[1] if old else None,
        "wef": f"{wef[3]}-{int(wef[2]):02d}-{int(wef[1]):02d}" if wef else None,
        "retrospective": "retrospective" in text,
        "pending": bool(PENDING.search(text)),
        "text": text,
    }


def parse_all(texts):
    """parse() each footnote in document order, resolving "ibid." to the previous footnote's instrument."""
    out, last = [], None
    for text in texts:
        r = parse(text)
        if r["ibid"]:
            r["instrument"] = last
        last = r["instrument"] or last
        out.append(r)
    return out
