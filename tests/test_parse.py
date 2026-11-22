"""T13 and T15 (KICKOFF.md): the official consolidated Constitution parsed into law files, with its footnotes,
and its history rebuilt backwards from them."""
from pathlib import Path

import pytest
import yaml

import constitution
from build_repo import build, git
from footnotes import parse, parse_all
from pdf import pages
from rebuild import rebuild

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
    files, notes, report, _ = constitution.parse(SAMPLE)
    assert files == {
        "preamble.md": "# PREAMBLE\n\nWE, THE PEOPLE OF INDIA, having resolved to constitute India into a SOVEREIGN "
                       "REPUBLIC;\n\nJUSTICE, social;\n",
        "part-i/README.md": "# PART I\n\nTHE UNION\n",
        "part-i/article-001.md": "# 1. Name of the Union.\n\n- (1) India shall be a Union of States.\n"
                                 "- (2) The States shall be as specified in the First Schedule.\n",
        "part-i/article-003.md": "# 3. New States.\n\nParliament may by law—\n- (a) form a new State; and\n"
                                 "- (b) such date as the President may fix:\n  - *Provided that* no Bill shall be introduced.\n",
        "schedule-1.md": "# FIRST SCHEDULE\n\n- 1. Andhra Pradesh\n",
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
    assert report["e1"]["words_match"] == report["e1"]["files"] == 3  # two articles and the Schedule


@pytest.fixture(scope="session")
def whole():
    if not PDF.exists():
        pytest.skip(f"{PDF.name} is not in sources/ (it isn't committed)")
    return constitution.parse(pages(PDF))


def test_whole_constitution(whole):
    files, notes, report, _ = whole
    e1, fn = report["e1"], report["footnotes"]
    assert e1["words_match"] == e1["files"] > 450, e1["words_differ"]
    assert report["schedules"] == 12 and "schedule-7.md" in files
    assert not e1["provisions_not_round_tripping"]
    assert not report["pages_with_unpaired_footnotes"]
    assert report["stray_closing_brackets"] <= 2  # the source's own: Sixth Schedule p. 330, Ninth Schedule p. 375
    assert fn["changes_understood"] >= 0.95 * fn["changes"], fn["not_understood"]
    assert not fn["markers_without_note"] and not fn["notes_without_marker"]


def test_whole_constitution_matches_m0(whole, tmp_path):
    """The Preamble and Article 15 come out exactly as M0 built them by hand, and their footnotes as M0 blames them."""
    files, notes, _, _ = whole
    repo = build(ROOT / "history" / "constitution.yaml", tmp_path / "repo")
    for path in ("preamble.md", "part-iii/README.md", "part-iii/article-015.md"):
        assert files[path] == (repo / path).read_text(encoding="utf-8"), path
    table = yaml.safe_load((ROOT / "tests" / "official" / "constitution" / "footnotes.yaml").read_text(encoding="utf-8"))
    for f in table["footnotes"]:
        line = next(n for n, text in enumerate(files[f["file"]].split("\n"), 1) if f["line"] in text)
        acts = {(n["instrument"], n["section"]) for n in notes.values() if [f["file"], line] in n["covers"]}
        assert acts == {(f["act"], str(f["section"]))}, f["line"]


def replay(amendments):
    state = {}
    for act in amendments:
        for section in act["sections"]:
            for path, text in section["files"].items():
                state.pop(path) if text is None else state.__setitem__(path, text)
    return state


def test_rebuild_sample(tmp_path):
    files, notes, _, trail = constitution.parse(SAMPLE)
    amendments, report = rebuild(files, notes, trail, "https://example.org")
    assert [(a["act"], [s["section"] for s in a["sections"]]) for a in amendments] == [
        ("The Constitution of India", [None]),
        ("The Constitution (Seventh Amendment) Act, 1956", ["2"]),
        ("The Constitution (Thirty-fifth Amendment) Act, 1974", ["2", "3"]),
        ("The Constitution (Thirty-sixth Amendment) Act, 1975", ["5"]),  # art. 2A omitted, in its own text
        ("The Constitution (Forty-second Amendment) Act, 1976", ["2"]),
    ]
    base = amendments[0]["sections"][0]["files"]
    assert "into a DEMOCRATIC REPUBLIC;" in base["preamble.md"]  # the words the footnote quotes
    assert "- (2) [before The Constitution (Seventh Amendment) Act, 1956, s. 2: not quoted in the footnote]" in base[
        "part-i/article-001.md"]  # "for cl. (2)" quotes nothing
    assert "- (a) form a new State;\n" in base["part-i/article-003.md"]  # "3[and]" came later
    assert "part-i/article-002a.md" not in base and amendments[3]["sections"][0]["files"] == {"part-i/article-002a.md": None}
    assert replay(amendments) == files
    history = {"law": "sample", "title": "A sample", "official": "https://example.org", "note": "Silver.",
               "amendments": amendments}
    (tmp_path / "h.yaml").write_text(yaml.safe_dump(history, allow_unicode=True, sort_keys=False), encoding="utf-8")
    repo = build(tmp_path / "h.yaml", tmp_path / "repo")
    message = git(repo, "log", "-1", "--format=%B", "--skip=1")
    assert "Enacted: unknown" in message and "In-Force: 1975-04-26" in message and "Omitted by" in message


def test_rebuild_whole_constitution(whole):
    """Replayed forwards, the rebuilt history gives today's text; its 1950 Article 15 is M0's, and its 1950 Preamble
    is M0's but for the footnote's misquote of the 42nd Amendment ("Unity of the Nation")."""
    files, notes, _, trail = whole
    gold = yaml.safe_load((ROOT / "history" / "constitution.yaml").read_text(encoding="utf-8"))
    amendments, report = rebuild(files, notes, trail, gold["official"])
    assert replay(amendments) == files
    base, m0 = amendments[0]["sections"][0]["files"], gold["amendments"][0]["sections"][0]["files"]
    assert base["part-iii/article-015.md"] == m0["part-iii/article-015.md"]
    assert base["preamble.md"] == m0["preamble.md"].replace("unity of the Nation", "Unity of the Nation")
    assert len(report["lost"]) <= 0.02 * sum(report["undone"].values()), report["lost"]


RTI = ROOT / "sources" / "rti-act-dopt-2025-11-18.txt"  # DoPT's consolidated text, extracted; not committed


def test_act_mode_on_the_rti_act():
    """The same parser on an Act gives M0's hand-built files, except where M0 departs from DoPT's text on
    purpose (the Gazette's words, notes in tests/official/rti-act/footnotes.yaml)."""
    if not RTI.exists():
        pytest.skip(f"{RTI.name} is not in sources/ (it isn't committed)")
    import re
    files, notes, report, _ = constitution.parse(re.split(r"\f|\n?=====PAGE \d+=====\n", RTI.read_text(encoding="utf-8")),
                                                 act=True)
    assert report["e1"]["words_match"] == report["e1"]["files"] == 33
    gold = {}
    for act in yaml.safe_load((ROOT / "history" / "rti-act.yaml").read_text(encoding="utf-8"))["amendments"]:
        for section in act["sections"]:
            gold.update(section["files"])
    assert set(files) == set(gold)
    differ = {path for path in files if files[path] != gold[path]}
    assert differ == {
        "preamble.md", "chapter-ii/section-004.md", "chapter-iii/section-013.md", "chapter-iv/section-016.md",
        "schedule-2.md",  # M0 follows the Gazette: "expedient", "suo motu", no "(24 of 2019)", "thereunder", entries 8, 27
    }


IBC = ROOT / "sources" / "ibc" / "2016-05-28-ibc-2016.pdf"


def test_gazette_margin_notes():
    """T12 on the Gazette's own layout: a section's heading and an Act's number are printed in the margin; the
    extractor runs them in where a consolidated text has them, including numbers queued below a line naming
    several Acts."""
    if not IBC.exists():
        pytest.skip(f"{IBC.name} is not in sources/ibc/ (it isn't committed)")
    from pypdf import PdfReader
    from pdf import gazette
    reader = PdfReader(IBC)
    first, lost = gazette(reader.pages[0])
    assert "1. Short title, extent and commencement.—(1) This Code may be called" in first and not lost
    second = gazette(reader.pages[1])[0]
    assert "2. Application.—The provisions of this Code shall apply to—" in second
    assert "Companies Act, 2013 (18 of 2013) or under any" in second and "Partnership Act, 2008 (6 of 2009);" in second
    fifth, lost = gazette(reader.pages[4])
    assert ("Indian Contract Act, 1872 (9 of 1872), the Indian Partnership Act, 1932 (9 of 1932)" in fifth
            and "Act, 1949 (XXXVIII of 1949);" in fifth and not lost)


def test_whole_ibc_as_gazetted():
    """The Insolvency and Bankruptcy Code, 2016 as gazetted: every section and Schedule, each file's words equal
    to its source's, and one margin note left unplaced ("Indian Penal" / "Code." wraps)."""
    if not IBC.exists():
        pytest.skip(f"{IBC.name} is not in sources/ibc/ (it isn't committed)")
    from pypdf import PdfReader
    from pdf import gazette
    texts, lost = zip(*(gazette(page) for page in PdfReader(IBC).pages))
    assert sum(lost, []) == ["45 of 1860."]
    files, _, report, _ = constitution.parse(list(texts), act=True)
    assert report["articles"] == 255 and report["schedules"] == 11 and not report.get("article_numbers_missing")
    assert report["e1"]["words_match"] == report["e1"]["files"] == 266
    assert "part-ii/chapter-i/README.md" in files and files["part-ii/README.md"].strip().endswith("CORPORATE PERSONS")


def test_ibc_reconstruction_to_2018(tmp_path):
    """T18 on the IBC: the Code as gazetted plus the 2017 and 2018 amending Acts, against IBBI's consolidated text
    of 17 Aug 2018. The failures are the known ones (notes/results.md): an ambiguous "after the words", a hyphen
    the Gazette's text layer lacks, and a proviso inside an Explanation, which contract 2 can't nest."""
    acts = [ROOT / "sources" / "ibc" / f"{name}.pdf" for name in (
        "2016-05-28-ibc-2016", "2018-01-18-amendment-act-2017", "2018-08-17-second-amendment-act-2018")]
    consolidated = ROOT / "sources" / "ibc" / "consolidated-2018-08-17.pdf"
    if not all(p.exists() for p in [*acts, consolidated]):
        pytest.skip("the IBC's PDFs are not in sources/ibc/ (they aren't committed)")
    from pdf import gazetted
    import reconstruct
    base = tmp_path / "code-2016"
    files = constitution.parse(gazetted(acts[0])[0], act=True)[0]
    for path, text in files.items():
        (base / path).parent.mkdir(parents=True, exist_ok=True)
        (base / path).write_text(text, encoding="utf-8")
    steps = []
    for act in acts[1:]:
        (tmp_path / f"{act.stem}.txt").write_text("\f".join(gazetted(act)[0]), encoding="utf-8")
        steps.append(str(tmp_path / f"{act.stem}.txt"))
    (tmp_path / "c.txt").write_text("\f".join(pages(consolidated)), encoding="utf-8")
    _, report = reconstruct.replay(base, [*steps, f"={tmp_path / 'c.txt'}"])
    outcomes = [a["outcome"] for a in report["amendments"]]
    assert len(outcomes) == 45 and outcomes.count("applied") >= 42 and outcomes.count("failed") <= 1
    check = report["checks"][0]
    assert check["files_same"] >= 201 and check["amended_same"] + check["amended_old_differences_only"] >= 35


def test_unglue_mends_words_the_text_layer_breaks():
    from pdf import unglue
    text = "the costs and the costs, thecosts; th e following, the following, the following; section 7or section 9"
    assert unglue([text]) == [
        "the costs and the costs, the costs; the following, the following, the following; section 7 or section 9"]
