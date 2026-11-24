"""T13 and T15 (KICKOFF.md): the official consolidated Constitution parsed into law files, with its footnotes,
and its history rebuilt backwards from them."""
import re
from datetime import date
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
    ("Ins. by the Constitution (Thirty-eighth Amendment) Act, 1975, s. 2 (with retrospective effect) and omitted by "
     "the Constitution (Forty-fourth Amendment) Act, 1978, s. 16 (w.e.f. 20-6-1979).",  # the first change's own date
     {"instrument": "The Constitution (Thirty-eighth Amendment) Act, 1975", "section": "2", "wef": None,
      "retrospective": True}),
    ("Subs. by the Constitution (Thirty-ninth Amendment) Act, 1975, s. 2 (w.e.f 10-8-1975).", {"wef": "1975-08-10"}),
    ("Ins. by the Sixth Schedule, to the Constitution (Amendment) Act, 1988 (67 of 1988), s. 2 (w.e.f. 31-11-1988).",
     {"instrument": "The Sixth Schedule to the Constitution (Amendment) Act, 1988", "wef": None}),  # no 31 November
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
    notes = parse_all(["Subs. by the Constitution (Eighty-eighth Amendment) Act, 2003, s. 3, for “articles 268 and 269” "
                       "(not enforced) and further subs. by the Constitution (One Hundred and First Amendment) Act, "
                       "2016, s. 10, for “articles 268, 268A and 269” (w.e.f. 16-9-2016).",
                       "Ins. by s. 10, ibid. (w.e.f. 16-9-2016)."])  # after a compound note, its later instrument
    assert notes[1]["instrument"] == "The Constitution (One Hundred and First Amendment) Act, 2016"


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


CLAUSES = [  # made up: two clauses omitted under one note, a renumbering, and what E1 can't see
    "CONTENTS",
    "THE CONSTITUTION OF INDIA\nPREAMBLE\nWE, THE PEOPLE OF INDIA, having resolved to constitute India",
    "PART I\nTHE UNION\n5. Example.—(1) A clause.\n1(2)* * * *\n1(3)* * * *\n2[(2) The last clause.]\n"
    "3[5A. Repealed laws.].—Omitted by the Constitution (Forty-third Amendment) Act, 1977, s. 2 (w.e.f. 13-4-1978).\n"
    "6. Glued.–The text—\n(a)first, as printed;\n(b) second, at *four rupees.\n7. Assam.—Text of Assam.\n"
    "7-I. Goa.—Special provision (to be\n"
    "1. Cls. (2) and (3) omitted by the Constitution (Seventh Amendment) Act, 1956, s. 2 (w.e.f. 1-11-1956).\n"
    "2. Cl. (4) renumbered as cl. (2) by the Constitution (Forty-fourth Amendment) Act, 1978, s. 3 (w.e.f. 1-8-1979).\n"
    "3. Ins. by the Constitution (Forty-second Amendment) Act, 1976, s. 4 (w.e.f. 3-1-1977).\n"
    "* Now two thousand rupees.",
    "read with article 7).\n\n* Paragraph 7 declared invalid.",
]


def test_parse_what_e1_cant_see():
    """An omitted article whose heading isn't bracketed (art. 226A), "371-I", a heading ended "–", a label glued to
    a lowercase word, a "*" note on a lowercase word ("*four"), a "(" left open above note 1 that is body, not a side
    note, and a "*" note whose marker is on another page: E1 passes on all of them, right or wrong."""
    files, notes, report, _ = constitution.parse(CLAUSES)
    assert {p: t for p, t in files.items() if "article-" in p} == {
        "part-i/article-005.md": "# 5. Example.\n\n- (1) A clause.\n- (2) The last clause.\n",
        "part-i/article-006.md": "# 6. Glued.\n\nThe text—\n- (a) first, as printed;\n- (b) second, at four rupees.\n",
        "part-i/article-007.md": "# 7. Assam.\n\nText of Assam.\n",
        "part-i/article-007i.md": "# 7-I. Goa.\n\nSpecial provision (to be read with article 7).\n",
    }
    assert [a["article"] for a in report["omitted_articles"]] == ["5A"] and notes["3.p*"]["covers"] == [
        ["part-i/article-006.md", 5]]
    assert report["pages_with_unpaired_footnotes"] == [4]  # "* Paragraph 7 ...", out of the body all the same


@pytest.fixture(scope="session")
def coi():
    if not PDF.exists():
        pytest.skip(f"{PDF.name} is not in sources/ (it isn't committed)")
    return pages(PDF)


@pytest.fixture(scope="session")
def whole(coi):
    return constitution.parse(coi)


def test_whole_constitution(whole):
    files, notes, report, _ = whole
    e1, fn = report["e1"], report["footnotes"]
    assert e1["words_match"] == e1["files"] > 450, e1["words_differ"]
    assert report["schedules"] == 12 and "schedule-7.md" in files
    assert not e1["provisions_not_round_tripping"]
    assert report["pages_with_unpaired_footnotes"] == [379]  # the Tenth Schedule's note on para. 7, marked a page before
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


def test_articles_against_the_table_of_contents(coi, whole):
    """E1 compares each article with its own source, so it can't see one glued to the article before (371-I) or an
    omitted one written as live (131A). The Constitution's own table of contents can: every article it lists is a
    file, and every one it lists in brackets is omitted."""
    files, _, report, _ = whole
    text = "\f".join(coi)
    contents = text[text.index("CONTENTS"):text.index("\nSCHEDULES")]
    listed = {(m[2] + m[3].replace("-", ""), bool(m[1]))  # "371-I.", "243Z-I.", "[226A. ...—Omitted.]"
              for m in re.finditer(r"(?m)^\s*(\[?)(\d+)\s*([A-Z-]*)\s*\.\s*(?=[A-Z]|$)", contents)}
    assert {n for n, gone in listed if not gone} == {
        re.search(r"article-0*(\w+)\.md", p)[1].upper() for p in files if "article-" in p}
    assert {n for n, gone in listed if gone} == {a["article"] for a in report["omitted_articles"]} | {
        str(n) for n in report["article_numbers_missing"]}  # art. 238, whose Part VII is omitted whole


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
    history = {"law": "sample", "title": "A sample", "official": "https://example.org", "note": "Silver.",
               "amendments": amendments}
    (tmp_path / "h.yaml").write_text(yaml.safe_dump(history, allow_unicode=True, sort_keys=False), encoding="utf-8")
    repo = build(tmp_path / "h.yaml", tmp_path / "repo")
    message = git(repo, "log", "-1", "--format=%B", "--skip=1")
    assert "Enacted: unknown" in message and "In-Force: 1975-04-26" in message and "Omitted by" in message


def test_rebuild_omitted_clauses_and_a_renumbering():
    """Two clauses omitted under one note come back once each, in order, where they were; undoing a renumbering
    changes the label and keeps the clause's text."""
    files, notes, _, trail = constitution.parse(CLAUSES)
    amendments, _ = rebuild(files, notes, trail, "https://example.org")
    placeholder = "[before The Constitution (Seventh Amendment) Act, 1956, s. 2: not quoted in the footnote]"
    assert amendments[0]["sections"][0]["files"]["part-i/article-005.md"] == (
        f"# 5. Example.\n\n- (1) A clause.\n- (2) {placeholder}\n- (3) {placeholder}\n- (4) The last clause.\n")
    assert replay(amendments[:2])["part-i/article-005.md"] == "# 5. Example.\n\n- (1) A clause.\n- (4) The last clause.\n"
    assert [(a["act"], list(a["sections"][0]["files"])) for a in amendments[2:4]] == [  # art. 5A, inserted, omitted
        ("The Constitution (Forty-second Amendment) Act, 1976", ["part-i/article-005a.md"]),
        ("The Constitution (Forty-third Amendment) Act, 1977", ["part-i/article-005a.md"])]


def test_brackets_opened_together_say_nothing_about_order():
    """A change inside another's brackets is placed after it. Not when both open at the same place ("3[4[15.]"):
    which came first can't be told. Nor when the outer one only renumbered what it encloses."""
    from rebuild import events
    o, c, e = constitution.OPEN, constitution.CLOSE, constitution.END
    trail = [("schedule-4.md", 3, f"{o}9.1{e}{o}9.2{e}15.{c}9.2{e} Nagaland {o}9.3{e}1{c}9.3{e}{c}9.1{e}"),
             ("schedule-4.md", 4, f"{o}9.4{e}16. Goa {o}9.5{e}2{c}9.5{e}{c}9.4{e}")]
    notes = {fid: {**parse(text), "covers": [["schedule-4.md", 3]]} for fid, text in (
        ("9.1", "Ins. by the State of Nagaland Act, 1962 (27 of 1962), s. 6 (w.e.f. 1-12-1963)."),
        ("9.2", "Entries 16 to 29 renumbered as entries 15 to 28 by the Jammu and Kashmir Reorganisation Act, 2019 "
                "(34 of 2019), s. 8 (w.e.f. 31-10-2019)."),
        ("9.3", "Subs. by the Nagaland Act, 1970, s. 2, for “2” (w.e.f. 1-1-1971)."),
        ("9.4", "Entries 15 to 28 renumbered as entries 16 to 29 by the Goa Act, 1987, s. 6 (w.e.f. 30-5-1987)."),
        ("9.5", "Subs. by the Goa Act, 2000, s. 2, for “1” (w.e.f. 1-1-2000)."))}
    parents = events(notes, trail)[1]
    assert (parents["9.2"], parents["9.3"], parents["9.5"]) == (set(), {"9.1"}, set())


def test_rebuild_whole_constitution(whole):
    """The rebuilt 1950 Article 15 is M0's, and its 1950 Preamble is M0's but for the footnote's misquote of the
    42nd Amendment ("Unity of the Nation"). Omitted clauses come back where they were, a renumbered clause keeps its
    text, and a change waits for a later one only where a table's brackets say so (notes/results.md)."""
    files, notes, _, trail = whole
    gold = yaml.safe_load((ROOT / "history" / "constitution.yaml").read_text(encoding="utf-8"))
    amendments, report = rebuild(files, notes, trail, gold["official"])
    base, m0 = amendments[0]["sections"][0]["files"], gold["amendments"][0]["sections"][0]["files"]
    assert base["part-iii/article-015.md"] == m0["part-iii/article-015.md"]
    assert base["preamble.md"] == m0["preamble.md"].replace("unity of the Nation", "Unity of the Nation")
    assert ("territory of India;\n  - (f) [before The Constitution (Forty-fourth Amendment) Act, 1978, s. 2: not quoted "
            "in the footnote]\n  - (g) to practise") in base["part-iii/article-019.md"]
    assert re.findall(r"(?m)^- \((\d)\)", base["part-vi/chapter-v/article-214.md"]) == ["2", "3"]
    before_44th = replay(amendments[:next(n for n, a in enumerate(amendments) if "Forty-fourth" in a["act"])])
    assert "\n- (7) The power conferred on a High Court" in before_44th["part-vi/chapter-v/article-226.md"]
    assert next(a["placed"] for a in amendments if "Thirty-eighth" in a["act"]).year == 1975
    late = [(a["act"], s["section"]) for a in amendments[1:] for s in a["sections"]
            if s.get("in_force") and a["placed"] > s["in_force"]]
    assert len(late) <= 5, late  # the 70th Amendment on art. 239AA, and four table rows in the First and Fourth Schedules
    assert len(report["lost"]) <= 0.02 * sum(report["undone"].values()), report["lost"]


RTI = ROOT / "sources" / "rti-act-dopt-2025-11-18.txt"  # DoPT's consolidated text, extracted; not committed


def test_act_mode_on_the_rti_act():
    """The same parser on an Act gives M0's hand-built files, except where M0 departs from DoPT's text on
    purpose (the Gazette's words, notes in tests/official/rti-act/footnotes.yaml)."""
    if not RTI.exists():
        pytest.skip(f"{RTI.name} is not in sources/ (it isn't committed)")
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


def test_act_mode_edges():
    """A long title that isn't "An Act to" and ends the page before "BE it enacted"; a section that says only that
    it's repealed; an omitted section rebuilt as a section, in a history that starts with the Act, not the
    Constitution."""
    files, notes, report, trail = constitution.parse([
        "ARRANGEMENT OF SECTIONS\n1. Short title.\n2. Penalty.",
        "THE EXAMPLE ACT, 2001\nAn Act further to amend the law\nrelating to examples.",
        "BE it enacted by Parliament as follows:—\n1. Short title.—This Act may be called the Example Act, 2001.\n"
        "2. Repealed by Act 1 of 2005.\n3. Penalty.—Whoever breaks it shall be punished.\n1[4. Fees.—A fee.]\n"
        "5. [Old.].—Omitted by Act 3 of 2010, s. 2 (w.e.f. 1-4-2010).\n1. Ins. by Act 2 of 2008, s. 3 (w.e.f. 1-1-2009).",
    ], act=True)
    assert sorted(files) == ["preamble.md", "section-001.md", "section-003.md", "section-004.md"]
    assert files["preamble.md"].startswith("An Act further to amend the law relating to examples.\n")
    assert [a["article"] for a in report["omitted_articles"]] == ["2", "5"]
    amendments, _ = rebuild(files, notes, trail, {}, "The Example Act, 2001", date(2001, 5, 1), None)
    assert amendments[0]["act"] == "The Example Act, 2001" and sorted(amendments[0]["sections"][0]["files"]) == [
        "preamble.md", "section-001.md", "section-003.md", "section-005.md"]


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
    text = "sub-\nsection (1), sub-\nsection (2) and subsection (3)"  # a line break after "sub-" isn't two words
    assert unglue([text]) == [text]


def test_pocso_rebuilt_back_and_replayed_forward(tmp_path):
    """T18 on POCSO: India Code's consolidated text parsed, its 2012 text rebuilt backwards from its footnotes,
    and the POCSO (Amendment) Act, 2019 replayed forwards on that, against the consolidated text. The files that
    still differ are the known ones (notes/results.md): instruments not to hand (s.1, s.42, s.42A), the Act's own
    typo "violance" (s.9), and s.4, which the footnotes can't rebuild."""
    current, amending = ROOT / "sources" / "pocso" / "2012-06-19-pocso-2012.pdf", ROOT / "sources" / "pocso" / "2019-08-05-amendment-act-2019.pdf"
    if not (current.exists() and amending.exists()):
        pytest.skip("POCSO's PDFs are not in sources/pocso/ (they aren't committed)")
    from pdf import gazetted
    import reconstruct
    files, provenance, report, trail = constitution.parse(pages(current), act=True)
    assert report["e1"]["words_match"] == report["e1"]["files"] and not report.get("article_numbers_missing")
    base = rebuild(files, provenance, trail, {}, "The Protection of Children from Sexual Offences Act, 2012",
                   date(2012, 6, 19), None)[0][0]["sections"][0]["files"]
    for name, law in (("current", files), ("base", base)):
        for path, text in law.items():
            (tmp_path / name / path).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / name / path).write_text(text, encoding="utf-8")
    (tmp_path / "act.txt").write_text("\f".join(gazetted(amending)[0]), encoding="utf-8")
    steps = [str(tmp_path / "act.txt"), f"={tmp_path / 'current'}"]
    cla13, cla18 = current.parent / "2013-04-02-criminal-law-amendment-act-2013-s29.txt", current.parent / "2018-08-11-criminal-law-amendment-act-2018.pdf"
    if cla13.exists() and cla18.exists():  # s.42 substituted by two sections in 2013, amended in 2018, then 2019
        (tmp_path / "cla-2018.txt").write_text("\f".join(gazetted(cla18)[0]), encoding="utf-8")
        steps = [str(cla13), f"{tmp_path / 'cla-2018.txt'}::Protection of Children from Sexual Offences Act", *steps]
    _, out = reconstruct.replay(tmp_path / "base", steps)
    differ = {p.split("/")[-1] for p in out["checks"][0]["differ"]}
    assert differ <= {"section-001.md", "section-004.md", "section-009.md", "section-042.md", "section-042a.md"}
    if len(steps) > 2:  # what's left in s.42 and s.42A is India Code's "only" and its "addition" for "additon"
        assert all(a["outcome"] == "applied" for a in out["amendments"][:2])


def test_arbitration_rebuilt_back_and_replayed_forward(tmp_path):
    """T18 on the Arbitration and Conciliation Act: India Code's text consolidated to the 2015 amendment, its 1996
    text rebuilt from its footnotes, and the Amendment Act, 2015 (Act 3 of 2016) replayed on that. Placeholders
    that stand for whole clauses ("for clauses (a) and (b)") keep it short of every file (notes/results.md)."""
    folder = ROOT / "sources" / "arbitration"
    current, amending = folder / "1996-08-16-arbitration-act-1996.pdf", folder / "2016-01-01-amendment-act-2015.pdf"
    if not (current.exists() and amending.exists()):
        pytest.skip("the Arbitration Act's PDFs are not in sources/arbitration/ (they aren't committed)")
    from pdf import gazetted
    import reconstruct
    files, provenance, report, trail = constitution.parse(pages(current), act=True)
    assert report["e1"]["words_match"] == report["e1"]["files"] and "section-001.md" in files
    base = rebuild(files, provenance, trail, {}, "The Arbitration and Conciliation Act, 1996", date(1996, 8, 16),
                   None)[0][0]["sections"][0]["files"]
    for name, law in (("current", files), ("base", base)):
        for path, text in law.items():
            (tmp_path / name / path).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / name / path).write_text(text, encoding="utf-8")
    (tmp_path / "act.txt").write_text("\f".join(gazetted(amending)[0]), encoding="utf-8")
    _, out = reconstruct.replay(tmp_path / "base", [str(tmp_path / "act.txt"), f"={tmp_path / 'current'}"])
    outcomes = [a["outcome"] for a in out["amendments"]]
    # s.25's four new Schedules fail: the rebuilt base already has the Fifth to Seventh (notes/results.md)
    assert outcomes.count("applied") >= 19 and out["checks"][0]["files_same"] >= 106
    gazette = folder / "1996-08-19-arbitration-act-1996-gazette.pdf"  # the Act as gazetted: checks the rebuilt base
    if gazette.exists():
        import difflib
        kept = {p: t for p, t in base.items() if not re.search(r"schedule-[567]", p)}  # the 2015 Act's (see notes)
        ours = [w for p in reconstruct.in_order(kept) for w in reconstruct.words(re.sub(r"^#+ |^\s*- |\*", "", kept[p], flags=re.M))]
        text = "".join(pages(gazette))
        theirs = reconstruct.words(text[text.find("WHEREAS"):])
        same = sum(b.size for b in difflib.SequenceMatcher(None, ours, theirs, autojunk=False).get_matching_blocks())
        assert same / len(ours) > 0.94
