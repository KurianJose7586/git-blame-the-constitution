"""T13 and T15 (KICKOFF.md): the official consolidated Constitution parsed into law files, with its footnotes."""
from pathlib import Path

import pytest
import yaml

import constitution
from build_repo import build
from footnotes import parse, parse_all
from pdf import pages

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources" / "coi-2026-09-10.pdf"


@pytest.mark.parametrize("text, want", [
    ("Subs. by the Constitution (Forty-second Amendment) Act, 1976, s.2, for “SOVEREIGN DEMOCRATIC REPUBLIC” "
     "(w.e.f. 3-1-1977).",
     {"kind": "substituted", "instrument": "The Constitution (Forty-second Amendment) Act, 1976", "section": "2",
      "old": "SOVEREIGN DEMOCRATIC REPUBLIC", "wef": "1977-01-03"}),
    ("The words “or Rajpramukh” omitted by the Constitution (Seventh Amendment) Act, 1956, s. 29 and Sch. "
     "(w.e.f. 1-11-1956).",
     {"kind": "omitted", "instrument": "The Constitution (Seventh Amendment) Act, 1956", "section": "29"}),
    ("Subs. by the Orissa (Alteration of Name) Act, 2011 (15 of 2011), s. 4, for “Orissa” (w.e.f. 1-11-2011).",
     {"instrument": "The Orissa (Alteration of Name) Act, 2011", "section": "4", "old": "Orissa"}),
    ("Sub-clause (i) re-lettered as sub-clause (j) by the Constitution (Seventy-fifth Amendment) Act, 1993, s. 2 "
     "(w.e.f. 15-5-1994).", {"kind": "relettered", "section": "2"}),
    ("Art 338A i n s .  by the Constitution ( Eighty-ninth Amendment) A c t , 2003, s. 3 (w.e.f. 19-2-2004).",
     {"kind": "inserted", "instrument": "The Constitution (Eighty-ninth Amendment) Act, 2003", "section": "3"}),
    ("Cl. (4) shall stand substituted by the Constitution (Forty-fourth Amendment) Act, 1978, s. 3 "
     "(date yet to be notified).", {"kind": "substituted", "pending": True, "wef": None}),
    ("Ins. by the Constitution (First Amendment) Act, 1951, s. 4, (with retrospective effect).",
     {"retrospective": True, "wef": None}),
    ("Subs. by C.O. 272, dated the 5-8-2019, s.2. for “Constituent Assembly” (w.e.f. 5-8-2019).",
     {"instrument": "C.O. 272"}),
    ("See the Constitution (Declaration as to Foreign States) Order, 1950 (C.O. 2).", {"kind": None}),
])
def test_footnote(text, want):
    got = parse(text)
    assert {k: got[k] for k in want} == want


def test_ibid_is_the_instrument_before():
    notes = parse_all(["Subs. by the Constitution (Seventh Amendment) Act, 1956, s. 2, for cl. (2) (w.e.f. 1-11-1956).",
                       "Subs. by s. 2, ibid., for sub-clause (b) (w.e.f. 1-11-1956).",
                       "Ins. ibid., s. 3 (w.e.f. 1-11-1956)."])
    assert [(n["instrument"], n["section"]) for n in notes] == [
        ("The Constitution (Seventh Amendment) Act, 1956", s) for s in ("2", "2", "3")]


SAMPLE = [
    "CONTENTS",
    "THE CONSTITUTION OF INDIA\nPREAMBLE\nWE, THE PEOPLE OF INDIA, having resolved to constitute\n"
    "India into a 1[SOVEREIGN REPUBLIC];\n\nJUSTICE, social;\n"
    "1. Subs. by the Constitution (Forty-second Amendment) Act, 1976, s.2, for “DEMOCRATIC REPUBLIC” (w.e.f. 3-1-1977).",
    "PART I\nTHE UNION\n1. Name of the Union.—(1) India shall be a Union of\nStates.\n"
    "1[(2) The States shall be as specified in the\nFirst Schedule.]\n"
    "2[2A. [Sikkim.].—Omitted by the Constitution (Thirty-sixth Amendment) Act, 1975, s. 5 (w.e.f. 26-4-1975).]\n"
    "3. New States.—Parliament may by law—\n(a) form a new State; 3[and]\n(b) such date4 as the\nPresident may fix:\n"
    "Provided that no Bill shall be introduced.\n"
    "1. Subs. by the Constitution (Seventh Amendment) Act, 1956, s. 2, for cl. (2) (w.e.f. 1-11-1956).\n"
    "2. Ins. by the Constitution (Thirty-fifth Amendment) Act, 1974, s. 2 (w.e.f. 1-3-1975).\n"
    "3. Ins. by s. 3, ibid. (w.e.f. 1-3-1975).\n4. 7-1-2004, vide notifn. number S.O. 21(E).\n2",
    "FIRST SCHEDULE\n1. Andhra Pradesh",
]


def test_parse_sample():
    files, notes, report = constitution.parse(SAMPLE)
    assert files == {
        "preamble.md": "# PREAMBLE\n\nWE, THE PEOPLE OF INDIA, having resolved to constitute India into a SOVEREIGN "
                       "REPUBLIC;\n\nJUSTICE, social;\n",
        "part-i/README.md": "# PART I\n\nTHE UNION\n",
        "part-i/article-001.md": "# 1. Name of the Union.\n\n- (1) India shall be a Union of States.\n"
                                 "- (2) The States shall be as specified in the First Schedule.\n",
        "part-i/article-003.md": "# 3. New States.\n\nParliament may by law—\n- (a) form a new State; and\n"
                                 "- (b) such date as the President may fix:\n  - *Provided that* no Bill shall be introduced.\n",
    }
    assert {k: (n["instrument"], n["covers"], n["words"]) for k, n in notes.items()} == {
        "2.1": ("The Constitution (Forty-second Amendment) Act, 1976", [["preamble.md", 3]], "SOVEREIGN REPUBLIC"),
        "3.1": ("The Constitution (Seventh Amendment) Act, 1956", [["part-i/article-001.md", 4]],
                "(2) The States shall be as specified in the First Schedule."),
        "3.2": ("The Constitution (Thirty-fifth Amendment) Act, 1974", [["art.2A"]],
                "2A. [Sikkim.].—Omitted by the Constitution (Thirty-sixth Amendment) Act, 1975, s. 5 (w.e.f. 26-4-1975)."),
        "3.3": ("The Constitution (Thirty-fifth Amendment) Act, 1974", [["part-i/article-003.md", 4]], "and"),
        "3.4": (None, [["part-i/article-003.md", 5]], None),
    }
    assert [a["article"] for a in report["omitted_articles"]] == ["2A"]
    assert report["e1"]["words_match"] == report["articles"] == 2


@pytest.fixture(scope="session")
def whole():
    if not PDF.exists():
        pytest.skip(f"{PDF.name} is not in sources/ (it isn't committed)")
    return constitution.parse(pages(PDF))


def test_whole_constitution(whole):
    files, notes, report = whole
    e1, fn = report["e1"], report["footnotes"]
    assert e1["words_match"] == e1["articles"] > 450, e1["words_differ"]
    assert not e1["provisions_not_round_tripping"]
    assert not report["pages_with_unpaired_footnotes"] and not report["stray_closing_brackets"]
    assert fn["changes_understood"] >= 0.95 * fn["changes"], fn["not_understood"]
    assert not fn["markers_without_note"] and not fn["notes_without_marker"]


def test_whole_constitution_matches_m0(whole, tmp_path):
    """The Preamble and Article 15 come out exactly as M0 built them by hand, and their footnotes as M0 blames them."""
    files, notes, _ = whole
    repo = build(ROOT / "history" / "constitution.yaml", tmp_path / "repo")
    for path in ("preamble.md", "part-iii/README.md", "part-iii/article-015.md"):
        assert files[path] == (repo / path).read_text(encoding="utf-8"), path
    table = yaml.safe_load((ROOT / "tests" / "official" / "constitution" / "footnotes.yaml").read_text(encoding="utf-8"))
    for f in table["footnotes"]:
        line = next(n for n, text in enumerate(files[f["file"]].split("\n"), 1) if f["line"] in text)
        acts = {(n["instrument"], n["section"]) for n in notes.values() if [f["file"], line] in n["covers"]}
        assert acts == {(f["act"], str(f["section"]))}, f["line"]
