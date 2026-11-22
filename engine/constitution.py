"""The official consolidated Constitution as law files (KICKOFF.md T13; its footnotes are T15).

    uv run engine/constitution.py out/coi.txt out/constitution-current
    uv run engine/constitution.py --act out/rti.txt out/rti-act-current       # an Act: sections, "CHAPTER I"

The input is the text ingest/pdf.py extracts from the Legislative Department's "The Constitution of India (as on
...)". The output is the Preamble and Parts I-XXII in contract 2's format (`part-iii/article-015.md`,
`part-v/chapter-i/README.md`), plus:

- provenance.json: every footnote, parsed, with the file lines its brackets cover. A footnote such as
  "Subs. ... for “X”" beside the bracketed new words is a reverse diff, which M2 rebuilds history from.
- report.json: what was left out of the files and why (omitted articles and clauses, sub-headings), what wasn't
  understood, and experiment E1's numbers.

The Schedules (tables and forms) come later.
"""
import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "ingest"))
from footnotes import parse_all  # noqa: E402
from ops import structure  # noqa: E402

# Footnote markers become tokens, which survive line joining, so each can be traced to the lines it covers:
# "1[" opens a bracket and its "]" closes it; "1* * *" marks an omission.
OPEN, CLOSE, POINT, END = "\x02", "\x04", "\x05", "\x03"
TOKEN = re.compile("([\x02\x04\x05])([^\x03]*)\x03")
HEADER = re.compile(r"^(?:\d+\s+)?THE CONSTITUTION OF INDIA$|^\((?:Part|.*Schedule|Appendix)\b.*\)$|^\d+$")
NOTE = re.compile(r"^(\d+)(?:\.\s*|\s+)(?=\S)|^(\uf02a+)\s*|^(\*+)\s+(?=[A-Z])")
NOTE_NEXT = re.compile(r"^(\d+)(?:\.\s*|\s+(?=[A-Z][a-z]))(?=\S)|^(\uf02a+)\s*|^(\*+)\s+(?=[A-Z])")
PART = re.compile(r"^PART\s+([IVXL]+[A-Z]?)$")
ORDINALS = "FIRST SECOND THIRD FOURTH FIFTH SIXTH SEVENTH EIGHTH NINTH TENTH ELEVENTH TWELFTH".split()
SCHEDULE = re.compile(rf"^(?:THE\s+)?({'|'.join(ORDINALS)})\s+SCHEDULE$")
ENTRY = re.compile(r"^(\d+[A-Z]*)(?:\.\s|\.?\s*\*)")  # a Schedule's paragraph or entry: "1. Interpretation.—", "18.* * *"
CHAPTER = re.compile(r"^CHAPTER\s+([IVXL]+)\.\s*—\s*(.*)$")
ACT_CHAPTER = re.compile(r"^CHAPTER\s+([IVXL]+[A-Z]?)$")
ENACTING = re.compile(r"^(?:An Act to|WHEREAS|AND WHEREAS|Now,?\s+THEREFORE|BE it enacted)")
ARTICLE = re.compile(r"^\[?(\d+)([A-Z]*)\.\s")  # "[232. Interpretation.—...]": an omitted article, bracketed
LABEL = re.compile(r"^\((\d+[A-Z]*|[a-z]{1,6}|[A-Z])\)(?=\s|\*|$|\()")  # "(f)* * *": an omitted clause
# A provision that opens with two labels, "(2)(a) There shall be" or "(3) (a) Subject to": clause (2) starts with
# its sub-clause (a). Split after the first label, so each can be cited, as art.239AA(2)(a).
DOUBLE = re.compile("^((?:[\x02\x04\x05][^\x03]*\x03)*\\(\\w{1,6}\\))\\s*(?=(?:[\x02\x04\x05][^\x03]*\x03)*\\(\\w{1,6}\\)(?:[\x02\x04\x05][^\x03]*\x03)*\\s)")
HEAD_END = re.compile("\\.((?:[\x02\x04\x05][^\x03]*\x03|\\])*)\\s*(?:—|-(?=\\s))")  # art. 330A ends its heading ".-"
DONE = re.compile(r"(?:[—:;.,*]|[;,]\s*(?:and|or))$")
OMISSION = re.compile(r"\s*\*(?:\s*\*){2,}")
ROMANS = "i ii iii iv v vi vii viii ix x xi xii xiii xiv xv xvi xvii xviii xix xx".split()


def flat(text):
    """Tokens out, wrapped lines joined ("sub-" / "clause" -> "sub-clause"), whitespace collapsed."""
    return " ".join(re.sub(r"(?<=-)\s*\n\s*", "", TOKEN.sub("", text)).split())


def join(a, b):
    return a + b if a.rstrip().endswith("-") else f"{a.rstrip()} {b.strip()}"


def caps(text):
    return bool(re.search("[A-Z]", text)) and text == text.upper()


def done(text):
    return bool(DONE.search(flat(text).rstrip(" ]\"”'")))


# --- Pages ------------------------------------------------------------------------------------------------

def clean(number, text):
    """A page's body lines with markers as tokens, its footnotes {"page.marker": text}, and whether they paired."""
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and (not lines[0].strip() or HEADER.match(lines[0].strip())):
        lines.pop(0)
    while lines and (not lines[-1].strip() or re.fullmatch(r"\d+", lines[-1].strip())):
        lines.pop()
    for i in range(len(lines)):  # the first place a footnote block can start whose notes all have markers
        m = NOTE.match(lines[i].strip())
        if not m or m[1] not in (None, "1"):  # a block starts with note 1 or a "*" note
            continue
        block = lines[i:]
        if i and lines[i - 1].count("(") > lines[i - 1].count(")"):
            # a side note set beside the first footnote ("(date yet to be" / "notified).") belongs to it
            block, i = [block[0], lines[i - 1], *block[1:]], i - 1
        notes = split_notes(block)
        body = "\n".join(lines[:i])
        if notes and any(k[0] == "p" for k in notes):  # "3*[239A." is note 3's bracket and note "*": "*3[239A."
            body = re.sub(r"(?<![\d(])(\d{1,2})(\*+)\[", r"\2\1[", body)
        body = notes and place(body, list(notes), number)
        if body:
            return body.split("\n"), {f"{number}.{k}": v for k, v in notes.items()}, True
    return lines, {}, not re.search(r"\d[\[*]|\uf02a", "\n".join(lines))  # paired if there was nothing to pair


def place(body, keys, page, ordered=True):
    """The body with each footnote's marker, found in page order, as a token; None if one can't be found.

    Most markers open a bracket ("4[all or any ...]") or mark an omission ("1* * *", "1(2)* * *"). A few are bare
    superscripts glued to a word ("such date4 as") or to an omitted article's number ("731D. [Saving ...]" is note 7
    on article 31D). A note can serve two markers: "2(2)* * * *" and "2(3)* * * *". A table's columns can come out
    of page order, so if the markers aren't all found in order, each is looked for from the top.
    """
    found, at = [], 0
    for k in keys:
        if not k.isdigit():  # asterisk notes come in their own order: look from the top
            m = strong(k).search(body)
            if not m:
                return None
            found.append((m, k))
            continue
        m = strong(k).search(body, at) or min(filter(None, (
            re.compile(rf"(?<=[A-Za-z.,;:)\]”’])(?<!s\.){k}(?=[\s,.;:])").search(body, at),
            re.compile(rf"(?m)^{k}(?=\d+[A-Z]*(?:\.\s+\[|\s*\*))").search(body, at))), key=lambda m: m.start(), default=None)
        # last resort, a note glued to a Schedule paragraph's number: "21. Autonomous districts" is note 2 on para. 1
        m = m or re.compile(rf"(?m)^{k}(?=\d+\.\s)").search(body, at)
        if not m:
            return place(body, keys, page, ordered=False) if ordered else None
        found.append((m, k))
        at = m.end() if ordered else 0
    for m, k in sorted(found, key=lambda f: -f[0].start()):
        body = body[:m.start()] + token(m, f"{page}.{k}") + body[m.end():]
    for k in keys:
        body = strong(k).sub(lambda m: token(m, f"{page}.{k}"), body)
    return body


def strong(k):
    """Note k's marker opening a bracket or marking an omission: "4[", "1* * *", "1(2)* * *".

    Notes "*", "**", ... are marked with runs of the glyph U+F02A."""
    if k[0] == "p":
        return re.compile(rf"(?<![\w*])\*{{{len(k) - 1}}}(?=\d{{1,2}}\[|[A-Z])")  # "*3[239A.", "of *Puducherry"
    if k[0] == "*":
        return re.compile(rf"(?<!\uf02a)\uf02a{{{len(k)}}}(?!\uf02a)\[?")
    return re.compile(rf"(?<![\d(]){k}(?:\[|(?=\*|\(\w+\)\s*\*))")


def token(m, fid):
    return f"{OPEN if m[0].endswith('[') else POINT}{fid}{END}"


def split_notes(lines):
    notes, key = {}, None
    for s in (line.strip() for line in lines if line.strip()):
        m = (NOTE if key is None else NOTE_NEXT).match(s)  # only the first may lack its dot: "1 Subs." but "1 S.C.C."
        n = m and (m[1] or ("*" * len(m[2]) if m[2] else "p" + m[3]))
        if m and (not n.isdigit() or n == str(sum(k.isdigit() for k in notes) + 1)):
            key, notes[n] = n, s[m.end():]
        elif re.match(r"\d{1,2}\.", s):  # note 2 where 1 was due: this block started in the wrong place
            return None
        elif key:
            notes[key] = join(notes[key], s)
        else:
            return None
    return notes


def brackets(stream, starts, never=frozenset()):
    """Each "]" that closes a marker's "[" becomes a closing token. Returns (stream, brackets never closed, stray "]").

    A bracket can span articles ("Arts. 350A and 350B ins."), but the source also leaves a few open: "census.]]"
    closes two of three. Called again with those (`never`), it closes each where the article, Chapter or Part it
    opened in ends; `starts` gives the stream index where each of those begins.
    """
    rank = {"article": 0, "chapter": 1, "part": 2}
    stack, out, stray, unclosed = [], [], 0, []
    for n, (page, line) in enumerate(stream):
        # No bracket crosses a Part or a Schedule, so one still open there was never closed: drop it now, or a stray
        # "]" far on would close it and stretch its note over everything between.
        for entry in [e for e in stack if n in starts and (e[2] in never and e[1] <= rank[starts[n]]
                                                           or starts[n] == "part")]:
            stack.remove(entry)
            if entry[2] not in never:
                unclosed.append(entry)
            last = max(k for k, (_, text) in enumerate(out) if flat(text))
            out[last] = (out[last][0], out[last][1] + (f"{CLOSE}{entry[0]}{END}" if entry[0] else ""))
        pieces = re.split(r"(\x02[^\x03]*\x03|\[|\])", line)
        for k, piece in enumerate(pieces):
            if piece.startswith(OPEN) or piece == "[":
                stack.append((piece[1:-1] if piece != "[" else None, rank.get(starts.get(n), 0), (n, k)))
            elif piece == "]" and stack:
                fid = stack.pop()[0]
                pieces[k] = f"{CLOSE}{fid}{END}" if fid else piece
            elif piece == "]":
                stray += 1
        out.append((page, "".join(pieces)))
    return out, unclosed + [e for e in stack if e[2] not in never], stray


def unstack(stream):
    """The oath forms print "solemnly affirm" on its own line under "swear in the name of God", as alternatives.
    Read in order it lands mid-sentence; put it beside them instead, as M0's RTI Act has it:
    "swear in the name of God / solemnly affirm". A label printed against its text, "(1)Where", gets its space."""
    out = []
    for page, line in stream:
        swear = out and re.search(r"swear\s+in\s+the\s+name\s+of\s+God", out[-1][1])
        if line.strip() == "solemnly affirm" and swear:
            prev = out[-1][1]
            out[-1] = (out[-1][0], prev[:swear.end()] + " / solemnly affirm" + prev[swear.end():])
        else:
            out.append((page, re.sub("((?:^|—)(?:[\x02\x04\x05][^\x03]*\x03)*\\(\\w{1,6}\\))(?=[A-Z])", r"\1 ", line)))
    return out


# --- Units: the Preamble, Parts, Chapters, sub-headings and articles ---------------------------------------

def key(match):
    return int(match[1]), match[2]  # 239 < 239A < 239AA < 239AB < 239B


def segment(stream, act=False):
    """(units, {stream index: "article", "chapter" or "part"} where each begins)."""
    units, starts, last, i = [], {}, (0, ""), 0
    texts = [flat(line) for _, line in stream]

    def article_at(j):
        m = j < len(texts) and ARTICLE.match(texts[j])
        return bool(m) and last < key(m) and key(m)[0] - last[0] <= 20 and bool(
            HEAD_END.search("\n".join(line for _, line in stream[j:j + 4])))

    def heading_at(j):
        return (0 < len(texts[j]) <= 80 and not DONE.search(texts[j]) and not LABEL.match(texts[j])
                and not ARTICLE.match(texts[j]) and not PART.match(texts[j]) and not CHAPTER.match(texts[j]))

    while i < len(stream):
        line, text = stream[i][1], texts[i]
        if not units:
            if text == "PREAMBLE" or act and text.startswith("An Act to"):
                units.append(["preamble", [] if text == "PREAMBLE" else [line]])
        elif m := SCHEDULE.match(text):
            units.append(["schedule", ORDINALS.index(m[1]) + 1, line, []])
            starts[i] = "part"
        elif units[-1][0] == "schedule":  # a Schedule runs to the next one: no Parts or articles inside
            units[-1][-1].append(line)
            if ENTRY.match(re.sub(r"[\[\]]", "", text)):  # "23.] Manipur": a bracket never closed closes here
                starts[i] = "article"
        elif m := PART.match(text):
            j = i + 1
            while (j < len(stream) and (not texts[j] or caps(texts[j])) and not CHAPTER.match(texts[j])
                   and not (act and ACT_CHAPTER.match(texts[j]))):
                j += 1
            units.append(["part", m[1], line, [s for _, s in stream[i + 1:j] if flat(s)], []])
            starts[i] = "part"
            i = j
            continue
        elif act and (m := ACT_CHAPTER.match(text)):  # "CHAPTER I" / "PRELIMINARY"
            j = i + 1
            while j < len(stream) and (not texts[j] or caps(texts[j])) and not article_at(j):
                j += 1
            units.append(["chapter", m[1], line, [s for _, s in stream[i + 1:j] if flat(s)]])
            starts[i] = "chapter"
            i = j
            continue
        elif m := CHAPTER.match(text):
            j = i + 1
            while j < len(stream) and caps(texts[j]) and not article_at(j):
                j += 1
            units.append(["chapter", m[1], line, [s for _, s in stream[i + 1:j]]])
            starts[i] = "chapter"
            i = j
            continue
        elif article_at(i):
            last = key(ARTICLE.match(text))
            units.append(["article", last, [line]])
            starts[i] = "article"
        elif heading_at(i) and (units[-1][0] in ("part", "chapter") or done(next(
                (s for s in reversed(units[-1][-1]) if flat(s)), ""))) and (
                article_at(i + 1) or (i + 1 < len(texts) and heading_at(i + 1) and article_at(i + 2))):
            n = 1 if article_at(i + 1) else 2
            units.append(["heading", [s for _, s in stream[i:i + n]]])
            i += n
            continue
        else:
            units[-1][-1].append(line)
        i += 1
    return units, starts


def provisions(lines):
    """Wrapped lines joined into provisions: a new one starts with a label or proviso once the last is complete."""
    out, seen = [], []
    for line in lines:
        text = flat(line)
        if not text:
            continue
        m = LABEL.match(text)
        starts = (m and (plausible(m[1], seen) or text[m.end():].lstrip().startswith("*"))  # "(2)* * *" stands
                  or text.startswith(("Provided", "Explanation")))
        if out and not (starts and done(out[-1])):
            out[-1] = join(out[-1], line.strip())
        else:
            out.append(line.strip())
        if m and starts:
            seen.append(m[1])
            if inner := LABEL.match(text[m.end():].lstrip()):
                seen.append(inner[1])
    split = []
    for p in out:
        d = DOUBLE.match(p)
        split += [d[1], p[d.end():]] if d else [p]
    return split


def plausible(label, seen):
    """A label that can come here: a first one, or the next after one already seen in this article."""
    if label in ("1", "a", "i", "A"):
        return True
    for last in seen:
        if label.startswith(last) or label in ROMANS and last in ROMANS and ROMANS.index(label) == ROMANS.index(last) + 1:
            return True
        if label.isdigit() and last.rstrip("ABCDEFGH").isdigit() and int(label) == int(last.rstrip("ABCDEFGH")) + 1:
            return True
        if len(label) == 1 and len(last) <= 2 and ord(label) == ord(last[0]) + 1:
            return True
    return False


def article(lines):
    """(heading's source, [(file line, source)] after the heading, [(text, source)] of omitted clauses)."""
    text = "\n".join(line for line in lines if flat(line))
    m = HEAD_END.search(text)
    head, body = text[:m.start() + 1] + m[1], text[m.end():]
    provs = [(" ".join(OMISSION.sub("", flat(p)).split()), p) for p in provisions(body.split("\n"))]
    first = next((n for n, (_, p) in enumerate(provs) if LABEL.match(flat(p)) or flat(p).startswith(
        ("Provided", "Explanation"))), len(provs))
    kept, omitted = [], []
    for words, p in provs[first:]:  # a clause that is only its label was omitted: "(f)* * * * *"
        gone = not words or re.fullmatch(r"\([^)\s]+\)", words) and "*" in flat(p)  # not "(2)" before "(a) ..."
        (omitted if gone else kept).append((words, p))
    lines = structure("\n".join(words for words, _ in kept)) if kept else []
    return head, provs[:first] + [("  " * depth + "- " + line, p) for (depth, line), (_, p) in zip(lines, kept)], omitted


HEAD = re.compile(r"^(?:PART\s+[A-Z]+|List\s+[IVX]+\b.*|[IVX]+|[A-Z]|TABLE"
                  r"|[\[(](?:See\s+)?(?:Articles?|[Pp]aragraphs?)\b.*[\])]\.?)$")  # "(Article 246)", "[Articles 1 and 4]"
LEADER = re.compile(r"\.{4,}|…")  # a table row: "1. Andhra Pradesh ........ 11"
WRAPS = re.compile(r"(?:\b(?:and|of|the|in|to|for|or|as|by)|,)$", re.I)


def schedule(lines):
    """A Schedule's lines as ([(file line, source)], [(text, source)] omitted). Headings ("PART A", "List I—Union
    List", "[Article 244(1)]", a form's number "III") are plain lines; entries and paragraphs ("1.", "(1)", "(a)")
    are lists, one per run between headings. A blank line has source None. Tables come out a row per line."""
    blocks = []  # [is_heading, [sources]]
    for line in lines:
        text = flat(line)
        if not text:
            continue
        prev = blocks[-1] if blocks else None
        heading = bool(HEAD.match(text) or caps(text) and not ENTRY.match(text))
        title = (prev and (prev[0] or re.search(r"[.:;—\])]$", flat(prev[1][-1]))) and len(text) <= 90
                 and text[0].isupper() and not done(text) and not (ENTRY.match(text) or LABEL.match(text))
                 )  # "Languages", "Validation of certain Acts and Regulations"
        starts = ENTRY.match(text) or LABEL.match(text) or text.startswith(("Provided", "Explanation", "“", '"'))
        wraps = WRAPS.search(flat(prev[1][-1])) or caps(flat(prev[1][-1])) and caps(text) if prev else False
        if prev and prev[0] and wraps and not HEAD.match(text) and not HEAD.match(flat(prev[1][-1])) and not starts:
            prev[1].append(line)  # a heading that wraps: "Provisions as to ... Scheduled Areas and" / "Scheduled Tribes"
        elif heading or title or not prev or prev[0] or starts and (done(prev[1][-1]) or LEADER.search(prev[1][-1])):
            blocks.append([bool(heading or title), [line]])
        else:
            prev[1][-1] = join(prev[1][-1], line.strip())
    out, omitted, run = [], [], []

    def flush():
        kept = []
        for p in run:
            words = " ".join(OMISSION.sub("", flat(p)).split())
            gone = not words or re.fullmatch(r"\([^)\s]+\)|\d+[A-Z]*", words.rstrip(". ")) and "*" in flat(p)  # "7. ***."
            (omitted if gone else kept).append((words, p))
        if kept:
            out.append(("", None))
            out.extend(("  " * depth + "- " + line, p) for (depth, line), (_, p) in
                       zip(structure("\n".join(w for w, _ in kept)), kept))
        run.clear()

    for is_heading, sources in blocks:
        if is_heading or not (ENTRY.match(flat(sources[0])) or LABEL.match(flat(sources[0])) or
                              flat(sources[0]).startswith(("Provided", "Explanation"))) and not run:
            flush()
            words = " ".join(OMISSION.sub("", flat("\n".join(sources))).split())
            if words:
                out += [("", None), (words, "\n".join(sources))]
            else:  # "* * * * *": a Part omitted
                omitted.append(("", "\n".join(sources)))
        else:
            run.extend(sources)
    flush()
    return out, omitted


# --- The whole document -----------------------------------------------------------------------------------

def parse(pages, act=False):
    """(files {path: text}, provenance {footnote id: record}, report, trail) from the extracted pages.

    The trail is every line of the document in order: (path, line number, source with markers as tokens), with
    path None and a label for what has no file (omitted articles, sub-headings). engine/rebuild.py reads it."""
    stream, notes, unpaired = [], {}, []
    start = next(i for i, text in enumerate(pages) if ("BE it enacted" if act else "WE, THE PEOPLE OF INDIA") in text)
    for i in range(start, len(pages)):
        body, page_notes, paired = clean(i + 1, pages[i])
        stop = next((j for j, line in enumerate(body)  # the Appendices, or a Bill's statement after an Act
                     if re.fullmatch(r"APPENDIX\s+I|STATEMENT OF OBJECTS AND REASONS", flat(line))), None)
        if not paired and stop is None:
            unpaired.append(i + 1)
        if stop is not None:  # the Appendices start on this page: their notes wait for an Appendix parser
            kept = {fid for line in body[:stop] for _, fid in TOKEN.findall(line)}
            page_notes = {k: v for k, v in page_notes.items() if k in kept}
        stream += [(i + 1, line) for line in body[:stop]]
        notes.update(page_notes)
        if stop is not None:
            break
    stream = unstack(stream)
    starts = segment(stream, act)[1]
    never = brackets(stream, starts)[1]
    stream, left, stray = brackets(stream, starts, {e[2] for e in never})
    units = segment(stream, act)[0]

    files, trail = {}, []  # trail: (path, line number, source) in document order; path None for what has no file
    report = {"pages": [stream[0][0], stream[-1][0]], "pages_with_unpaired_footnotes": unpaired,
              "brackets_never_closed": [e[0] or "[" for e in never], "brackets_left_open": len(left), "stray_closing_brackets": stray,
              "articles": 0, "omitted_articles": [], "omitted_provisions": [], "omitted_parts": [],
              "sub_headings": [], "e1": {}}
    part = chapter = None
    numbers, e1_ok, e1_bad, rt_ok, rt_bad = [], 0, [], 0, []

    def put(path, text, source):
        files.setdefault(path, []).append(text)
        trail.append((path, len(files[path]), source))

    for unit in units:
        kind = unit[0]
        if kind == "preamble" and act:  # "An Act to ...", "WHEREAS ...", ..., "BE it enacted ... as follows:—"
            paras = []
            for line in unit[1]:
                if flat(line) and (ENACTING.match(flat(line)) or not paras):
                    paras.append([line])
                elif flat(line):
                    paras[-1].append(line)
            for n, para in enumerate(paras):
                if n:
                    files["preamble.md"].append("")
                put("preamble.md", flat("\n".join(para)), "\n".join(para))
        elif kind == "preamble":
            put("preamble.md", "# PREAMBLE", "")
            paras, buf = [], []
            for line in unit[1] + [""]:
                if line.strip():
                    buf.append(line)
                elif buf:
                    paras.append(buf)
                    buf = []
            for para in paras:
                files["preamble.md"].append("")
                put("preamble.md", flat("\n".join(para)), "\n".join(para))
        elif kind in ("part", "chapter"):
            num, line, title = unit[1], unit[2], unit[3]
            if kind == "part":
                part, chapter = f"part-{num.lower()}", None
                if not title:  # an omitted Part: its bracketed former title and the note
                    report["omitted_parts"].append({"part": num, "text": flat("\n".join(unit[4])) or None})
                    trail.append((None, f"PART {num}", "\n".join([line] + unit[4])))
                    continue
                path = f"{part}/README.md"
            else:
                chapter = f"{part}/chapter-{num.lower()}" if part else f"chapter-{num.lower()}"
                path = f"{chapter}/README.md"
                title = title if act else [line.split("—", 1)[1]] + title
            put(path, f"# {kind.upper()} {num}", line)
            files[path].append("")
            put(path, " ".join(OMISSION.sub("", flat("\n".join(title))).split()), "\n".join(title))  # "THE STATES * * *"
        elif kind == "schedule":
            path = f"schedule-{unit[1]}.md"
            put(path, f"# {flat(unit[2])}", unit[2])  # as printed: "FIRST SCHEDULE", "THE FIRST SCHEDULE"
            lines, omitted = schedule(unit[3])
            report["schedules"] = report.get("schedules", 0) + 1
            for text, source in lines:
                if source is None:
                    files[path].append(text)
                else:
                    put(path, text, source)
            for words, source in omitted:
                report["omitted_provisions"].append({"schedule": unit[1], "text": words})
                trail.append((None, f"sch.{unit[1]}", source))
            if e1_words("\n".join(unit[3])) == e1_words("\n".join(files[path][1:])):
                e1_ok += 1
            else:
                e1_bad.append(path)
            good, bad = round_trip(files[path])
            rt_ok += good
            rt_bad += [f"{path}: {line}" for line in bad]
        elif kind == "heading":
            report["sub_headings"].append(flat("\n".join(unit[1])))
            trail.append((None, "sub-heading", "\n".join(unit[1])))
        elif kind == "article":
            head, lines, omitted = article(unit[2])
            heading = " ".join(OMISSION.sub("", flat(head)).split())  # "the States of * * * Maharashtra"
            number = ARTICLE.match(heading)
            label = f"{number[1]}{number[2]}"
            numbers.append(int(number[1]))
            body_text = flat("\n".join(source for _, source in lines))
            if heading.startswith("[") or heading.split(" ", 1)[1].startswith("[") and body_text.startswith(
                    ("Omitted", "Rep.")):
                report["omitted_articles"].append({"article": label, "text": flat("\n".join(unit[2]))})
                trail.append((None, f"art.{label}", "\n".join(unit[2])))
                continue
            report["articles"] += 1
            path = f"{chapter or part}/{'section' if act else 'article'}-{int(number[1]):03d}{number[2].lower()}.md"
            put(path, f"# {heading}", head)
            files[path].append("")
            for text, source in lines:
                put(path, text, source)
            for words, source in omitted:
                report["omitted_provisions"].append({"article": label, "text": words})
                trail.append((None, f"art.{label}", source))
            if e1_words("\n".join(unit[2])) == e1_words("\n".join(files[path])):
                e1_ok += 1
            else:
                e1_bad.append(path)
            good, bad = round_trip(files[path])
            rt_ok += good
            rt_bad += [f"{path}: {line}" for line in bad]

    gaps = [n for a, b in zip(numbers, numbers[1:]) for n in range(a + 1, b)]
    report["article_numbers_missing"] = gaps
    report["e1"] = {"files": report["articles"] + report.get("schedules", 0), "words_match": e1_ok, "words_differ": e1_bad,
                    "provisions_round_trip": rt_ok, "provisions_not_round_tripping": rt_bad}

    # Provenance: which lines each footnote's brackets cover, walking the document in order.
    ids = list(notes)
    parsed = dict(zip(ids, parse_all([notes[i] for i in ids])))
    covers = {i: [] for i in ids}
    spans = {}
    open_now = set()
    for path, number, source in trail:
        hit = set(open_now)
        for kind, fid in TOKEN.findall(source):
            hit.add(fid)
            if kind == OPEN:
                open_now.add(fid)
            elif kind == CLOSE:
                open_now.discard(fid)
        for fid in hit:
            if fid in covers:
                covers[fid].append([path, number] if path else [number])
        for fid, words in re.findall("\x02([^\x03]*)\x03(.*?)\x04\\1\x03", source, re.S):
            spans[fid] = flat(words)
    provenance = {i: {**parsed[i], "page": int(i.split(".")[0]), "marker": i.split(".")[1], "covers": covers[i],
                      "words": spans.get(i)} for i in ids}
    used = {fid for _, _, s in trail for _, fid in TOKEN.findall(s)}
    changes = [i for i in ids if parsed[i]["kind"]]
    report["footnotes"] = {
        "total": len(ids),
        "changes": len(changes),
        "changes_understood": sum(1 for i in changes if parsed[i]["instrument"]),
        "changes_with_date": sum(1 for i in changes if parsed[i]["wef"]),
        "changes_pending": [i for i in changes if parsed[i]["pending"]],
        "not_understood": [f"{i}: {notes[i]}" for i in changes if not parsed[i]["instrument"]],
        "other_notes": [f"{i}: {notes[i][:100]}" for i in ids if not parsed[i]["kind"]],
        "markers_without_note": sorted(used - set(ids)),
        "notes_without_marker": [i for i in ids if i not in used],
    }
    return {path: "\n".join(lines) + "\n" for path, lines in files.items()}, provenance, report, trail


def e1_words(text):
    """Words, for E1: markers, Markdown, dashes and omission stars out; omitted clauses' labels out with them."""
    text = re.sub(r"(?<=\.)-(?=\s)", " ", TOKEN.sub("", text))  # a heading ended ".-" (art. 330A)
    text = re.sub(r"(?m)(?:\([^)\s]{1,6}\)|^\s*\d+[A-Z]*\.?)\s*(?:\*\s*){3,}\.?$", "", text)  # "(f)* * *", "7. ***."
    text = OMISSION.sub("", text)
    text = re.sub(r"(?<=-)[ \t]*\n\s*", "", text)
    text = re.sub(r"^\s*(?:#|-) ", "", text, flags=re.M)
    return re.sub(r"[*\[\]]", "", text).replace("—", " ").replace(")(", ") (").split()  # "(2)(a)" is two labels


def round_trip(lines):
    """(provisions that read back the same, [those that don't]): each of a file's lists, re-read by structure()."""
    good, bad, items = 0, [], []
    for line in lines + [""]:
        if m := re.match(r"^( *)- (.*)$", line):
            items.append((len(m[1]) // 2, m[2]))
            continue
        if items:  # a list ends where a plain line starts: a Schedule has one per heading
            plain = [re.sub(r"^\*(Provided[^*]*|Explanation)\*", r"\1", text) for _, text in items]
            wrong = [text for (d, text), again in zip(items, structure("\n".join(plain))) if (d, text) != again]
            good, bad, items = good + len(items) - len(wrong), bad + wrong, []
    return good, bad


if __name__ == "__main__":
    act = "--act" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--act"]
    if len(args) != 2:
        sys.exit(__doc__)
    pages = re.split(r"\f|\n?=====PAGE \d+=====\n", Path(args[0]).read_text(encoding="utf-8"))
    files, provenance, report, _ = parse(pages, act)
    out = Path(args[1])
    for path, text in files.items():
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_text(text, encoding="utf-8", newline="\n")
    (out / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    e1, fn = report["e1"], report["footnotes"]
    print(f"{len(files)} files, {report['articles']} articles, {report.get('schedules', 0)} Schedules; E1 words {e1['words_match']}/{e1['files']}, "
          f"round trip {e1['provisions_round_trip']}/{e1['provisions_round_trip'] + len(e1['provisions_not_round_tripping'])}"
          f" provisions; {fn['total']} footnotes, {fn['changes_understood']}/{fn['changes']} changes understood")
