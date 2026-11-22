"""Text from PDFs, page by page (KICKOFF.md T12).

    uv run ingest/pdf.py sources/coi-2026-09-10.pdf out/coi.txt
    uv run ingest/pdf.py --gazette sources/ibc/2016-05-28-ibc-2016.pdf out/ibc/ibc-2016.txt   # an Act as gazetted

Born-digital pages give their text layer. A page without one is a scan: it comes back empty and is listed by
`scanned()`, so the caller can send it to OCR (not built yet) instead of silently losing it.
"""
import re
import sys

from pypdf import PdfReader

PAGE_BREAK = "\f"
SAME_LINE = 6  # points; footnote markers sit about 5 above their line, lines are about 16 apart


def pages(path):
    return [text(page) for page in PdfReader(path).pages]


def text(page):
    """The page's text, its lines in reading order.

    pypdf follows the content stream, which sometimes draws a line out of place (the Constitution's page 252 draws
    "India." above the heading it ends). So each line is placed by its height on the page and sorted top to bottom.
    If the lines can't be matched to heights one for one, the stream order is kept.
    """
    heights = []  # per line: [lowest y, last y, last x]

    def visit(chunk, cm, tm, font, size):
        if chunk.strip():
            x, y = tm[4] * cm[0] + tm[5] * cm[2] + cm[4], tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            if heights and abs(heights[-1][1] - y) < SAME_LINE and x >= heights[-1][2] - 1:
                heights[-1] = [min(heights[-1][0], y), y, x]
            else:  # lower, higher, or back at the left: a new line
                heights.append([y, y, x])

    raw = page.extract_text(visitor_text=visit) or ""
    lines = [line for line in raw.split("\n") if line.strip()]
    order = sorted(range(len(lines)), key=lambda i: -heights[i][0]) if len(lines) == len(heights) else None
    if order is None or order == sorted(order):
        return raw
    return "\n".join(lines[i] for i in order)


MARGIN = (100, 480)  # points: a Gazette page's body runs between its margin notes (x about 58 and 489)
CITATION = re.compile(r"^((?:\d+|[IVXLC]+) (?:of|to) (\d{4}))\.?$")  # an Act's number: "18 of 2013.", "XXXVIII of 1949."
YEAR = re.compile(r"(?:Act|Code|Procedure|Ordinance|Regulations?|Order)(?:,\s*|\s+)\d{4}\b|,\s*\d{4}\b"
                  r"|Penal Code\b")  # cited without its year
SIGNED = re.compile(r"Secretary to the Gov(?:t\.|ernment)\s+of\s+India\.?")  # the whole line: the signature


def gazette(page):
    """A Gazette page's body as text, with its margin notes where a consolidated text has them.

    A section's heading, printed in the margin beside its first line, is run into that line ("2. Application.—The
    provisions ..."); an Act's number, printed in the margin beside its name, follows the name ("Companies Act, 2013
    (18 of 2013)"). The running header goes, and so does everything from the signature on. Returns (text, notes
    that found no place)."""
    runs = []

    def visit(chunk, cm, tm, font, size):
        if chunk.strip():
            runs.append((tm[4] * cm[0] + tm[5] * cm[2] + cm[4], tm[4] * cm[1] + tm[5] * cm[3] + cm[5],
                         chunk.replace("\n", "").replace(chr(0xFFFD), "—")))  # some fonts lose the dash's mapping

    page.extract_text(visitor_text=visit)

    def lines(chunks):  # [[y, text]] top to bottom, each line's chunks left to right
        rows = []
        for x, y, chunk in sorted(chunks, key=lambda r: -r[1]):
            if not rows or abs(rows[-1][0] - y) >= 3:
                rows.append([y, []])
            rows[-1][1].append((x, chunk))
        return [[y, re.sub(r"\(\s+(?=\w)|(?<=\w)\s+\)", lambda m: m[0].strip(),  # the text layer's "( 5)"
                           " ".join("".join(c for _, c in sorted(cs)).split()))] for y, cs in rows]

    inside = [MARGIN[0] <= x < MARGIN[1] for x, _, _ in runs]
    body = lines([r for r, i in zip(runs, inside) if i])
    margin = [lines([r for r in runs if r[0] < MARGIN[0]]), lines([r for r in runs if r[0] >= MARGIN[1]])]
    words = set(re.findall(r"[a-z]+", " ".join(t for _, t in body).lower()))

    def joined(parts):  # a heading's margin lines: "insol-" / "vency" is "insolvency", "Time-" / "limit" stays
        out = parts[0]
        for part in parts[1:]:
            m = re.search(r"([A-Za-z]+)-$", out)
            if m and (m[1] + re.match("[A-Za-z]*", part)[0]).lower() in words:
                out = out[:-1] + part
            else:
                out += part if m else " " + part
        return out

    if body and "GAZETTE OF INDIA" in body[0][1]:
        body[0][1] = ""
    for i, (_, text) in enumerate(body):
        if SIGNED.fullmatch(text):
            body = body[:i - 1 if i and re.fullmatch(r"[A-Z][A-Z. ]+,", body[i - 1][1]) else i]
            break

    lost, citations, inserts = [], [], {}  # inserts: {body row: [(position, text)]}
    for side in margin:  # each margin on its own, so a citation on one side doesn't cut a heading on the other
        for k in range(len(side) - 1, 0, -1):  # a citation in two lines: "XXXVIII of" / "1949."
            if re.fullmatch(r"(?:\d+|[IVXLC]+) (?:of|to)", side[k - 1][1]) and re.fullmatch(r"\d{4}\.?", side[k][1]):
                side[k - 1][1] += " " + side.pop(k)[1]
        heading = []
        for y, text in side + [(None, "")]:
            if heading and (y is None or CITATION.match(text) or heading[-1][0] - y > 11):  # the heading ends here
                title = joined([t for _, t in heading])
                starts = [n for n, (by, bt) in enumerate(body)
                          if abs(by - heading[0][0]) < 5 and re.match(r"[“\"]?\d+[A-Z]*\.", bt)]
                if starts:
                    n = min(starts, key=lambda n: abs(body[n][0] - heading[0][0]))
                    m = re.match(r"[“\"]?\d+[A-Z]*\.\s*", body[n][1])
                    inserts.setdefault(n, []).append((m.end(), ("" if m[0][-1] == " " else " ") + f"{title}—"))
                else:
                    lost.append(title)
                heading = []
            if m := CITATION.match(text):
                citations.append((y, m))
            elif text:
                heading.append((y, text))
    # An Act's number sits beside its name, or lower when one line names several Acts and the numbers queue up.
    # Each goes after the nearest name at or above it, one of the same year first ("6 of 2009" is the LLP Act, 2008).
    names = [(n, hit) for n, (_, text) in enumerate(body) for hit in YEAR.finditer(text)]
    taken, placed = set(), set()  # names cited, citations placed
    for same_year in (True, False):
        for c, (y, m) in sorted(enumerate(citations), key=lambda c: -c[1][0]):
            fits = [(n, hit) for n, hit in names if (n, hit.start()) not in taken and c not in placed
                    and (-4 if same_year else -16) <= body[n][0] - y <= 60  # or a line down: "Indian" / "Penal Code"
                    and (not same_year or hit[0][-4:] == m[2])]
            if fits:
                n, hit = min(fits, key=lambda f: (body[f[0]][0] - y < -4, abs(body[f[0]][0] - y), -f[1].start()))
                taken.add((n, hit.start()))
                placed.add(c)
                inserts.setdefault(n, []).append((hit.end(), f" ({m[1]})"))
    lost += [m[0] for c, (_, m) in enumerate(citations) if c not in placed]
    for n, edits in inserts.items():
        text = body[n][1]
        for position, extra in sorted(edits, reverse=True):
            text = text[:position] + extra + text[position:]
        body[n][1] = text
    return "\n".join(text for _, text in body if text and not re.fullmatch(r"[—-]+", text)), lost


def scanned(texts, min_chars=40):
    """1-based numbers of the pages with no usable text layer."""
    return [n for n, text in enumerate(texts, 1) if len(text.strip()) < min_chars]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--gazette"]
    if len(args) != 2:
        sys.exit(__doc__)
    if "--gazette" in sys.argv:
        texts, lost = [], []
        for n, page in enumerate(PdfReader(args[0]).pages, 1):
            text, missed = gazette(page)
            texts.append(text)
            lost += [f"p. {n}: {note}" for note in missed]
        print("\n  ".join(["margin notes with no place:"] + lost) if lost else "every margin note placed")
    else:
        texts = pages(args[0])
    with open(args[1], "w", encoding="utf-8", newline="\n") as f:
        f.write(PAGE_BREAK.join(texts))
    missing = scanned(texts)
    print(f"{len(texts)} pages, {len(texts) - len(missing)} with text" + (f"; scanned: {missing}" if missing else ""))
