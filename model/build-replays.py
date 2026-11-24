"""T18's outputs from sources/ alone: every out/ path model/build-silver.sh reads, and the Constitution's parse and
silver history (notes/results.md). Run from the repository's root; OUT defaults to out/.

    uv run model/build-replays.py [OUT]

Each step is the command notes/results.md gives: ingest/pdf.py for text (--gazette for an Act as gazetted),
engine/constitution.py for law files, engine/rebuild.py for the Constitution's history. POCSO's and the Arbitration
Act's texts as enacted are rebuilt backwards from their consolidations' footnotes, as tests/test_parse.py does. The
IBC's 2019 Act is its hand transcription; POCSO's 2013 excerpt is read from sources/ by build-silver.sh itself.
"""
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "engine"), str(ROOT / "ingest")]
from constitution import parse  # noqa: E402
from rebuild import rebuild  # noqa: E402

SRC, OUT = ROOT / "sources", Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out")


def run(script, *args):
    subprocess.run([sys.executable, str(ROOT / script), *map(str, args)], check=True)


def text(pdf, txt, gazette=False):
    txt.parent.mkdir(parents=True, exist_ok=True)
    run("ingest/pdf.py", *(["--gazette"] if gazette else []), pdf, txt)


def law(txt, folder, act=True):  # a folder of its own: no file left from an earlier parse
    shutil.rmtree(folder, ignore_errors=True)
    run("engine/constitution.py", *(["--act"] if act else []), txt, folder)


def enacted(txt, folder, act, assent):  # the Act as enacted, rebuilt backwards from its consolidation's footnotes
    files, provenance, _, trail = parse(txt.read_text(encoding="utf-8").split("\f"), act=True)
    shutil.rmtree(folder, ignore_errors=True)
    for path, body in rebuild(files, provenance, trail, {}, act, assent, None)[0][0]["sections"][0]["files"].items():
        (folder / path).parent.mkdir(parents=True, exist_ok=True)
        (folder / path).write_text(body, encoding="utf-8", newline="\n")


assert (SRC / "pocso" / "2013-04-02-criminal-law-amendment-act-2013-s29.txt").exists()  # build-silver.sh reads it

text(SRC / "coi-2026-09-10.pdf", OUT / "coi.txt")
law(OUT / "coi.txt", OUT / "constitution-current", act=False)
run("engine/rebuild.py", OUT / "coi.txt", OUT / "constitution-silver.yaml")

G = OUT / "ibc" / "g"
for name in ("2016-05-28-ibc-2016", "2018-01-18-amendment-act-2017", "2018-08-17-second-amendment-act-2018",
             "2020-03-13-amendment-act-2020", "2020-09-23-second-amendment-act-2020", "2021-08-12-amendment-act-2021"):
    text(SRC / "ibc" / f"{name}.pdf", G / f"{name}.txt", gazette=True)
shutil.copy(SRC / "ibc" / "2019-08-06-amendment-act-2019.transcribed.txt", G / "2019-08-06-amendment-act-2019.txt")
for pdf in sorted((SRC / "ibc").glob("consolidated-*.pdf")):
    text(pdf, OUT / "ibc" / f"{pdf.stem}.txt")
law(G / "2016-05-28-ibc-2016.txt", OUT / "ibc" / "code-2016")

P = OUT / "pocso"
text(SRC / "pocso" / "2019-08-05-amendment-act-2019.pdf", P / "2019-08-05-amendment-act-2019.txt", gazette=True)
text(SRC / "pocso" / "2018-08-11-criminal-law-amendment-act-2018.pdf", P / "cla-2018.txt", gazette=True)
text(SRC / "pocso" / "2012-06-19-pocso-2012.pdf", P / "indiacode-2023.txt")  # India Code's text as of 28 Feb 2023
law(P / "indiacode-2023.txt", P / "current")
enacted(P / "indiacode-2023.txt", P / "silver-2012", "The Protection of Children from Sexual Offences Act, 2012",
        date(2012, 6, 19))

A = OUT / "arbitration"
for name in ("2016-01-01-amendment-act-2015", "2019-08-09-amendment-act-2019", "2021-03-11-amendment-act-2021"):
    text(SRC / "arbitration" / f"{name}.pdf", A / f"{name}.txt", gazette=True)
text(SRC / "arbitration" / "1996-08-16-arbitration-act-1996.pdf", A / "thc-1996.txt")  # consolidated to 2015
law(A / "thc-1996.txt", A / "current")
enacted(A / "thc-1996.txt", A / "silver-1996", "The Arbitration and Conciliation Act, 1996", date(1996, 8, 16))
text(SRC / "arbitration" / "2021-03-11-consolidated-wipo.pdf", A / "wipo-2021.txt")
law(A / "wipo-2021.txt", A / "current-2021")
