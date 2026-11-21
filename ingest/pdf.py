"""Text from PDFs, page by page (KICKOFF.md T12).

    uv run ingest/pdf.py sources/coi-2026-09-10.pdf out/coi.txt

Born-digital pages give their text layer. A page without one is a scan: it comes back empty and is listed by
`scanned()`, so the caller can send it to OCR (not built yet) instead of silently losing it.
"""
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


def scanned(texts, min_chars=40):
    """1-based numbers of the pages with no usable text layer."""
    return [n for n, text in enumerate(texts, 1) if len(text.strip()) < min_chars]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    texts = pages(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
        f.write(PAGE_BREAK.join(texts))
    missing = scanned(texts)
    print(f"{len(texts)} pages, {len(texts) - len(missing)} with text" + (f"; scanned: {missing}" if missing else ""))
