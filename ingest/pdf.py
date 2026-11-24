"""Text from PDFs, page by page (KICKOFF.md T12).

    uv run ingest/pdf.py sources/coi-2026-09-10.pdf out/coi.txt
    uv run ingest/pdf.py --gazette sources/ibc/2016-05-28-ibc-2016.pdf out/ibc/ibc-2016.txt   # an Act as gazetted

Born-digital pages give their text layer. A page without one is a scan: it comes back empty and is listed by
`scanned()`, so it isn't silently lost; in --gazette mode a scan is read by OCR (Tesseract).
"""
import csv
import io
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

TESSERACT = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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
CITATION = re.compile(r"^((?:Ord\.\s*)?(?:\d+|[IVXLC]+) (?:of|to) (\d{4}))\.?$")  # "18 of 2013.", "XXXVIII of 1949.", "Ord. 7 of 2017."
YEAR = re.compile(r"(?:Act|Code|Procedure|Ordinance|Regulations?|Order)(?:,\s*|\s+)\d{4}\b|,\s*\d{4}\b"
                  r"|Penal Code\b"  # cited without its year
                  r"|^\d{4}\b")  # a name that wraps before its year: "Ordinance," / "2017"
SIGNED = re.compile(r"Secretary to the Gov(?:t\.|ernment)\s+of\s+India\.?")  # the whole line: the signature
SECTION = re.compile(r"[“\"‘']?\d+(?:-?[A-Z]+)?\.\s*")  # "2. ", "29A. ", "54-I. " (the hyphen keeps I from 1)


def gazette(page):
    """A Gazette page's body as text, with its margin notes where a consolidated text has them.

    A section's heading, printed in the margin beside its first line, is run into that line ("2. Application.—The
    provisions ..."); an Act's number, printed in the margin beside its name, follows the name ("Companies Act, 2013
    (18 of 2013)"). The running header goes, and so does everything from the signature on. Returns (text, notes
    that found no place). A scanned page is read by OCR, its words placed the same way."""
    runs = []

    def visit(chunk, cm, tm, font, size):
        if chunk.strip():
            runs.append((tm[4] * cm[0] + tm[5] * cm[2] + cm[4], tm[4] * cm[1] + tm[5] * cm[3] + cm[5],
                         chunk.replace("\n", "")))

    page.extract_text(visitor_text=visit)
    if not runs:
        runs = ocr(page)

    def lines(chunks):  # [[y, text]] top to bottom, each line's chunks left to right
        rows = []
        for x, y, chunk in sorted(chunks, key=lambda r: -r[1]):
            if not rows or abs(rows[-1][0] - y) >= 3:
                rows.append([y, []])
            rows[-1][1].append((x, chunk))
        return [[y, tidy(" ".join("".join(c for _, c in sorted(cs, key=lambda c: c[0])).split()))]  # ties: as drawn
                for y, cs in rows]

    def tidy(text):  # typesetting in the text layer: "( 5)", a Bill's "––" for "—", "re- numbered"
        text = re.sub(r"\(\s+(?=\w)|(?<=\w)\s+\)", lambda m: m[0].strip(), text)
        return re.sub(r"(?<=\w)(?:- | -)(?=[A-Za-z])", "-", text.replace("––", "—"))

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
    starts = [n for n, (_, text) in enumerate(body) if SECTION.match(text)]  # "2. ", or a quoted "29A. " in an amendment
    for side in margin:  # each margin on its own, so a citation on one side doesn't cut a heading on the other
        for k in range(len(side) - 1, 0, -1):  # a citation in two lines: "XXXVIII of" / "1949."
            if re.fullmatch(r"(?:Ord\.\s*)?(?:\d+|[IVXLC]+) (?:of|to)", side[k - 1][1]) and re.fullmatch(r"\d{4}\.?", side[k][1]):
                side[k - 1][1] += " " + side.pop(k)[1]
        for k in range(len(side) - 1, -1, -1):  # a citation and a heading in one run: "31 of 2016. Amendment"
            if m := re.fullmatch(r"((?:\d+|[IVXLC]+) (?:of|to) \d{4}\.)\s+(\S.*)", side[k][1]):
                side[k:k + 1] = [[side[k][0], m[1]], [side[k][0], m[2]]]
        heading = []
        for y, text in side + [(None, "")]:
            level = y is not None and any(abs(body[n][0] - y) < 5 for n in starts)
            if heading and (y is None or CITATION.match(text) or heading[-1][0] - y > 11
                            or level and heading[-1][1].endswith(".")):  # the heading ends; the next may start here
                title = joined([t for _, t in heading])
                beside = [n for n in starts if abs(body[n][0] - heading[0][0]) < 5]
                if beside:
                    n = min(beside, key=lambda n: abs(body[n][0] - heading[0][0]))
                    m = SECTION.match(body[n][1])
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


def ocr(page):
    """Runs (x, y, text) of a scanned page, in points, read by Tesseract from the page's JPEG: each word at the
    height of its line, so a line's words stay together and margin notes split off by position as on a digital
    page. Tesseract is found on PATH, or where its Windows installer puts it."""
    jpegs = [x.get_object() for x in page["/Resources"].get("/XObject", {}).values()
             if "/DCTDecode" in str(x.get_object().get("/Filter"))]
    if not jpegs:
        return []
    with tempfile.TemporaryDirectory() as folder:
        image = Path(folder) / "page.jpg"
        image.write_bytes(jpegs[0]._data)
        tsv = subprocess.run([TESSERACT, str(image), "-", "-l", "eng", "--psm", "4", "tsv"], capture_output=True,
                             encoding="utf-8", check=True).stdout
    scale, height = float(page.mediabox.width) / int(jpegs[0]["/Width"]), float(page.mediabox.height)
    runs, line_y = [], {}
    for word in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if word["level"] == "5" and word["text"].strip():
            y = line_y.setdefault((word["block_num"], word["par_num"], word["line_num"]), height - int(word["top"]) * scale)
            runs.append((int(word["left"]) * scale, y, word["text"] + " "))
    return runs


def unglue(texts):
    """Words the text layer runs together ("thecosts", "partyto", "Insection"), split where the halves stand side by
    side elsewhere in the same document at least twice, and at least twice as often as the run-together form."""
    found = re.findall(r"[A-Za-z]+(?:-\s*[A-Za-z]+)*", " ".join(texts))  # "co-operate", "sub-" / "section": one word
    words = Counter(w.lower() for w in found)
    pairs = Counter(f"{a} {b}".lower() for a, b in zip(found, found[1:]))

    def split(m):
        word = m[0]
        for i in range(2, len(word) - 1):  # two letters a side: not "money s"
            if pairs[f"{word[:i]} {word[i:]}".lower()] >= max(2, 2 * words[word.lower()]):
                return f"{word[:i]} {word[i:]}"
        return word

    def join(m):  # the opposite: "th e following", "substitut ed", where the first part is no word of its own
        a, b = m[1], m[2]
        return a if words[a.lower()] == 1 and words[(a + b).lower()] >= 3 else m[0]  # drop the space only
    texts = [re.sub(r"\b(\d+)(or|and)\b", r"\1 \2", text) for text in texts]  # "section 7or section 9"
    texts = [re.sub(r"\b([A-Za-z]{2,}) (?=([a-z]{1,9})\b)", join, text) for text in texts]  # each pair, overlapping
    return [re.sub(r"[A-Za-z]{4,}(?![-A-Za-z])", split, text) for text in texts]  # not "recommenda-"


def gazetted(path):
    """(page texts, margin notes with no place) of a Gazette PDF."""
    texts, lost = [], []
    for n, page in enumerate(PdfReader(path).pages, 1):
        text, missed = gazette(page)
        texts.append(text)
        lost += [f"p. {n}: {note}" for note in missed]
    return unglue(texts), lost


def scanned(texts, min_chars=40):
    """1-based numbers of the pages with no usable text layer."""
    return [n for n, text in enumerate(texts, 1) if len(text.strip()) < min_chars]


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--gazette"]
    if len(args) != 2:
        sys.exit(__doc__)
    if "--gazette" in sys.argv:
        texts, lost = gazetted(args[0])
        print("\n  ".join(["margin notes with no place:"] + lost) if lost else "every margin note placed")
    else:
        texts = pages(args[0])
    with open(args[1], "w", encoding="utf-8", newline="\n") as f:
        f.write(PAGE_BREAK.join(texts))
    missing = scanned(texts)
    unmapped = [n for n, text in enumerate(texts, 1) if chr(0xFFFD) in text]  # a glyph the font maps to no character
    print(f"{len(texts)} pages, {len(texts) - len(missing)} with text" + (f"; scanned: {missing}" if missing else "")
          + (f"; U+FFFD on pages {unmapped}" if unmapped else ""))
