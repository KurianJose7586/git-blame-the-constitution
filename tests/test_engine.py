"""M1 (KICKOFF.md T14, T16, T17): the executor, the regex baseline, and the replay of M0's hand-written history."""
import json
import random
from pathlib import Path

import pytest
import yaml

from ops import EditError, apply, check, file_id, nodes, structure
from replay import replay

ROOT = Path(__file__).resolve().parents[1]
ART = """# 15. Heading.

- (1) The State shall not discriminate against any citizen.
- (2) No citizen shall be subject to any disability with regard to—
  - (a) access to shops; or
  - (b) the use of wells.
  - *Provided that* nothing here applies to wells.
- (3) Nothing in this article shall prevent the State.
"""
F = {"part-iii/article-015.md": ART}


def run(*ops):
    return apply(F, list(ops))["part-iii/article-015.md"]


def test_ids_are_cited_like_lawyers_cite_them():
    assert [n[0] for n in nodes(ART)] == ["(1)", "(2)", "(2)(a)", "(2)(b)", "(2)/proviso", "(3)"]
    assert [file_id(p) for p in ("preamble.md", "part-iii/article-021a.md", "chapter-ii/section-008.md", "schedule-2.md")] == [
        "preamble", "art.21A", "s.8", "sch.2"]


def test_word_operations_stay_inside_their_target():
    out = run({"op": "SUBSTITUTE_WORDS", "target": "art.15(2)", "old": "citizen", "new": "person"})
    assert "No person shall" in out and "against any citizen" in out
    out = run({"op": "OMIT_WORDS", "target": "art.15(1)", "text": "against any citizen"})
    assert "- (1) The State shall not discriminate.\n" in out
    out = run({"op": "INSERT_WORDS", "target": "art.15(2)(a)", "position": "after", "anchor": "shops", "text": "and hotels"})
    assert "access to shops and hotels; or" in out


def test_node_operations():
    out = run({"op": "INSERT_NODE", "target": "art.15(2)(a)", "position": "after", "block": "(aa) access to parks; or"})
    assert "  - (a) access to shops; or\n  - (aa) access to parks; or\n  - (b)" in out
    out = run({"op": "SUBSTITUTE_NODE", "target": "art.15(2)", "block": "(2) No person shall—\n(a) enter;\nProvided that this is new."})
    assert "- (2) No person shall—\n  - (a) enter;\n  - *Provided that* this is new.\n- (3)" in out
    out = run({"op": "ADD_AT_END", "target": "art.15", "block": "(4) A new clause."})
    assert out.endswith("- (3) Nothing in this article shall prevent the State.\n- (4) A new clause.\n")
    out = run({"op": "OMIT_NODE", "target": "art.15(2)(b)"})
    assert "(b)" not in out and "  - *Provided that*" in out
    assert "- (4) Nothing in this article" in run({"op": "RENUMBER", "target": "art.15(3)", "label": "4"})


def test_errors_say_what_is_wrong():
    with pytest.raises(EditError, match=r"not found; nearest is 'against any citizen\.?'"):
        run({"op": "SUBSTITUTE_WORDS", "target": "art.15(1)", "old": "against any citizens", "new": "x"})
    with pytest.raises(EditError, match=r"art\.15\(7\): not found"):
        run({"op": "OMIT_NODE", "target": "art.15(7)"})
    with pytest.raises(EditError, match="has no label"):
        run({"op": "RENUMBER", "target": "art.15(2)/proviso", "label": "4"})
    with pytest.raises(EditError, match="expected"):
        run({"op": "OMIT_NODE", "target": "art.15(1)", "extra": 1})


def test_blocks_get_depth_from_their_labels():
    assert structure("(5) Salaries—\n(a) of the Chief;\n(b) of others:\nProvided that x:\nProvided further that y.") == [
        (0, "(5) Salaries—"), (1, "(a) of the Chief;"), (1, "(b) of others:"),
        (1, "*Provided that* x:"), (1, "*Provided further that* y.")]
    # "(i)" after "(h)" is clause i; "(i)" followed by "(ii)" is a sub-clause
    assert [d for d, _ in structure("(h) h;\n(i) clause i;\n(j) j—\n(i) one;\n(ii) two;")] == [0, 0, 0, 1, 1]
    assert structure("(15) Sashtra Seema Bal.", schedule=True) == [(0, "15. Sashtra Seema Bal.")]


def current(law):
    files = {}
    for act in yaml.safe_load((ROOT / "history" / f"{law}.yaml").read_text(encoding="utf-8"))["amendments"]:
        for sec in act["sections"]:
            files.update(sec["files"])
    return {p: t for p, t in files.items() if t and file_id(p)}


@pytest.mark.parametrize("law", ["constitution", "rti-act"])
def test_random_edits_never_touch_anything_outside_their_target(law):
    rng, files = random.Random(7), current(law)
    for _ in range(300):
        path = rng.choice(sorted(files))
        if not (found := nodes(files[path])):
            continue
        suffix, first, end, _ = rng.choice(found)
        target, words = file_id(path) + suffix, files[path].split("\n")[first].split()[2:]
        op = rng.choice([{"op": "OMIT_NODE", "target": target},
                         {"op": "INSERT_NODE", "target": target, "position": rng.choice(["after", "before"]), "block": "(zz) Inserted."},
                         {"op": "RENUMBER", "target": target, "label": "99"},
                         *([{"op": "SUBSTITUTE_WORDS", "target": target, "old": rng.choice(words), "new": "ZZZ"}] if words else [])])
        try:
            after = apply(files, [op])[path].split("\n")
        except EditError:
            continue
        before = files[path].split("\n")
        tail = len(before) - end
        assert after[:first] == before[:first] and after[len(after) - tail:] == before[end:], (target, op["op"])


def test_replay_of_m0_history():
    results = replay(ROOT / "history" / "constitution.yaml") + replay(ROOT / "history" / "rti-act.yaml")
    match = {r["amendment"]: r["match"] for r in results}
    assert len(results) == 16 and not any(r["misses"] or r["error"] for r in results)
    assert sum(m == "exact" for m in match.values()) == 12
    # The four that aren't exact, each explained in notes/results.md:
    assert match["The Constitution (One Hundred and Third Amendment) Act, 2019, s. 2"] == "quotes"  # straight quotes typed
    assert match["Notification No. G.S.R. 726(E), dated 8 October 2008"] == "words"  # full stop outside the quote
    assert match["Notification No. G.S.R. 673(E), dated 8 July 2016"] == "words"  # likewise
    assert match["The Digital Personal Data Protection Act, 2023, s. 44(3)"] is None  # keeps the proviso DoPT drops

    assert all(check(op) is None for r in results for op in r["ops"])  # every op the baseline made fits the schema


def test_baseline_reads_the_ibc_drafting():
    """Held-out drafting from the IBC's amending Acts (T18): context that follows the list's labels, "the words,
    figures and letter", "at both the places", the marginal heading, whole sections and two sub-sections at once."""
    from baseline import baseline
    ops, misses = baseline(
        'In section 30 of the principal Act,—\n'
        '(i) in sub-section (1), after the words "resolution plan", the words, figures and letter "along with an '
        'affidavit stating that he is eligible under section 29A" shall be inserted;\n'
        '(ii) in sub-section (2),—\n'
        '(A) in clauses (a) and (b), for the word "repayment" at both the places where it occurs, the word "payment" '
        'shall be substituted;\n'
        '(iii) in the marginal heading, for the word "Approval", the word "Approvals" shall be substituted.')
    assert not misses
    assert [(o["op"], o["target"], o.get("every")) for o in ops] == [
        ("INSERT_WORDS", "s.30(1)", None), ("SUBSTITUTE_WORDS", "s.30(2)", True), ("SUBSTITUTE_WORDS", "s.30/heading", None)]
    ops, _ = baseline('After section 29 of the principal Act, the following section shall be inserted, namely:—\n'
                      '"29A. Persons not eligible to be resolution applicant.—A person shall not be eligible.".')
    assert ops[0]["op"] == "INSERT_NODE" and ops[0]["target"] == "s.29" and ops[0]["block"].startswith("29A.")
    ops, _ = baseline('In section 21 of the principal Act, for sub-sections (7) and (8), the following sub-sections '
                      'shall be substituted, namely:—\n"(7) The Board may specify.\n(8) Save as otherwise provided.".')
    assert [(o["op"], o["target"]) for o in ops] == [("OMIT_NODE", "s.21(8)"), ("SUBSTITUTE_NODE", "s.21(7)")]


def test_executor_adds_sections_and_chapters():
    files = {"part-ii/chapter-iii/section-054.md": "# 54. Dissolution.\n\n- (1) Text.\n",
             "part-ii/chapter-iii/README.md": "# CHAPTER III\n\nLIQUIDATION\n"}
    got = apply(files, [{"op": "INSERT_NODE", "target": "s.54", "position": "after",
                         "block": "54Z. New section.—A person shall—\n(a) do this; and\n(b) do that."}])
    assert got["part-ii/chapter-iii/section-054z.md"] == "# 54Z. New section.\n\nA person shall—\n- (a) do this; and\n- (b) do that.\n"
    got = apply(files, [{"op": "INSERT_NODE", "target": "s.54", "position": "after", "block":
                         "CHAPTER III-A PRE-PACKAGED PROCESS\n54A. Eligible debtors.—(1) An application.\n54B. Duties.—Text."}])
    assert got["part-ii/chapter-iii-a/README.md"] == "# CHAPTER III-A\n\nPRE-PACKAGED PROCESS\n"
    assert {"part-ii/chapter-iii-a/section-054a.md", "part-ii/chapter-iii-a/section-054b.md"} <= set(got)
    assert "part-ii/chapter-iii/section-054.md" not in apply(files, [{"op": "OMIT_NODE", "target": "s.54"}])
    got = apply(files, [{"op": "SUBSTITUTE_NODE", "target": "s.54", "block": "54. Old.—Text.\n54A. New.—More."}])
    assert got["part-ii/chapter-iii/section-054.md"] == "# 54. Old.\n\nText.\n"  # one section for two (POCSO s.42)
    assert got["part-ii/chapter-iii/section-054a.md"] == "# 54A. New.\n\nMore.\n"
    got = apply(files, [{"op": "INSERT_NODE", "target": "s.54", "position": "after", "block":  # Arbitration 2019
                         "PART IIA COUNCIL\n54A. Definitions.—Text.\n54B. Council.—More."}])
    assert got["part-iia/README.md"] == "# PART IIA\n\nCOUNCIL\n" and "part-iia/section-054b.md" in got


def test_executor_adds_and_omits_schedules_and_portions():
    files = {"schedule-7.md": "# THE SEVENTH SCHEDULE\n\nText.\n", "section-011.md": SECTION_11}
    block = "‘THE EIGHTH SCHEDULE (See section 43J) Qualifications\n(i) is an advocate; or\n(ii) is an accountant."
    got = apply(files, [{"op": "INSERT_NODE", "target": "sch.7", "position": "after", "block": block}])
    assert got["schedule-8.md"].startswith("# THE EIGHTH SCHEDULE\n") and "- (ii) is an accountant." in got["schedule-8.md"]
    assert "schedule-8.md" not in apply(got, [{"op": "OMIT_NODE", "target": "sch.8"}])
    two = apply(files, [{"op": "INSERT_NODE", "target": "sch.7", "position": "after",
                         "block": "THE EIGHTH SCHEDULE Text. THE NINTH SCHEDULE More."}])  # the 2015 Act: four in one
    assert {"schedule-8.md", "schedule-9.md"} <= set(two)
    got = apply(files, [{"op": "SUBSTITUTE_WORDS", "target": "s.11(4)", "old": "the appointment shall be made",
                         "to": "designated by such Court", "new": "the institution shall appoint"}])
    assert "third arbitrator, the institution shall appoint;" in got["section-011.md"]


SECTION_11 = """# 11. Appointment of arbitrators.

- (4) If the procedure applies and—
  - (a) a party fails to appoint; or
  - (b) the two fail to agree on the third arbitrator, the appointment shall be made by any person designated by such Court;
"""


def test_baseline_reads_schedules_parts_portions_and_ranges():
    from baseline import baseline
    assert baseline("After the Seventh Schedule to the principal Act, the following Schedule shall be inserted, namely:—\n"
                    "“THE EIGHTH SCHEDULE Text.”.")[0][0] == {
        "op": "INSERT_NODE", "target": "sch.7", "position": "after", "block": "THE EIGHTH SCHEDULE Text."}
    assert baseline("The Eighth Schedule to the principal Act shall be omitted.")[0] == [{"op": "OMIT_NODE", "target": "sch.8"}]
    assert baseline("After Part I of the principal Act, the following Part shall be inserted, namely:—\n"
                    "“PART IA COUNCIL 43A. Definitions.—Text.”.")[0][0]["target"] == "s.43"
    ops = baseline("In section 11 of the principal Act,—\n(ii) in sub-section (4), in the long line, for the portion "
                   "beginning with ‘‘the appointment shall be made’’ and ending with ‘‘designated by such Court’’, the "
                   "following shall be substituted, namely:—\n‘‘the institution shall appoint’’;\n"
                   "(ix) for sub-sections (11) to (14), the following sub-sections shall be substituted, namely:—\n"
                   "“(11) Text.”.")[0]
    assert ops[0] == {"op": "SUBSTITUTE_WORDS", "target": "s.11(4)", "old": "the appointment shall be made",
                      "to": "designated by such Court", "new": "the institution shall appoint"}
    assert [op["target"] for op in ops[1:]] == ["s.11(14)", "s.11(13)", "s.11(12)", "s.11(11)"]
    assert baseline('In the Fourth Schedule, for the brackets, words and figures "[See section 11 (14)]", the brackets, '
                    'words and figures "[See section 11(3A)]" shall be substituted.')[0][0]["target"] == "sch.4"  # not quoted


def test_examples_show_the_law_and_round_trip():
    """M2.md T19: the input shows the files a provision names, line by line with IDs; targets in the output are
    those IDs, and the output applied gives the law the operations did."""
    from examples import example, named
    assert named("In section 30 of the principal Act, for “section 7 or 9”, the words “sections 7, 9 and 10” "
                 "shall be substituted; the Fourth Schedule") == {"s.30", "sch.4"}
    law = {"part-iii/article-014.md": "# 14. Equality.\n\nText.\n", **F}
    ops = [{"op": "SUBSTITUTE_WORDS", "target": "art.15/proviso", "old": "wells", "new": "tanks"}]  # found by fallback
    source, output, targets, shown, after = example(law, "Amendment of article 15.", "In article 15, in the proviso, ...", ops)
    assert "art.15(2)/proviso\t  - *Provided that* nothing here applies to wells." in source
    assert "art.14\t# 14. Equality." in source and "Text." not in source.split("---")[1]  # a neighbour: its heading
    parsed = json.loads(output)
    assert parsed[0]["target"] == "art.15(2)/proviso" and shown and "art.15(2)/proviso" in targets
    assert after == apply(law, parsed) == apply(law, ops)
    assert named("in sub-section 3 of section 38, sections 40 to 42") == {"s.38", "s.40", "s.41", "s.42"}


def test_words_that_occur_twice_need_every():
    with pytest.raises(EditError, match="occurs 2 times"):
        run({"op": "SUBSTITUTE_WORDS", "target": "art.15", "old": "wells", "new": "tanks"})
    assert run({"op": "SUBSTITUTE_WORDS", "target": "art.15", "old": "wells", "new": "tanks", "every": True}).count("tanks") == 2
    with pytest.raises(EditError, match="not found"):  # whole words only: "hops" isn't in "shops"
        run({"op": "SUBSTITUTE_WORDS", "target": "art.15(2)(a)", "old": "hops", "new": "x"})


def test_baseline_reads_the_2026_drafting():
    """Drafting first met in the IBC (Amendment) Act, 2026, after its held-out count (notes/results.md)."""
    from baseline import baseline
    ops, misses = baseline(
        'In section 5 of the principal Act,—\n'
        '(a) clause (2A) shall be re-numbered as clause (2B) thereof and before clause (2B) as so re-numbered, the '
        'following clause shall be inserted, namely:—\n‘(2A) "avoidance transaction" means a transaction;’;\n'
        '(b) in clause (15), after the words "process period" occurring at the end, the words "and such other debt" '
        'shall be inserted;\n'
        '(c) clauses (ze), (zf) and (zg) shall be omitted.')
    assert not misses
    assert [(o["op"], o["target"], o.get("label") or o.get("last") or o.get("position")) for o in ops] == [
        ("RENUMBER", "s.5(2A)", "2B"), ("INSERT_NODE", "s.5(2B)", "before"), ("INSERT_WORDS", "s.5(15)", True),
        ("OMIT_NODE", "s.5(ze)", None), ("OMIT_NODE", "s.5(zf)", None), ("OMIT_NODE", "s.5(zg)", None)]
    assert [o["target"] for o in baseline("Sections 38, 39 and 42 of the principal Act shall be omitted.")[0]] == [
        "s.38", "s.39", "s.42"]
    ops, _ = baseline('In section 217 of the principal Act,—\n(a) for the marginal heading, the marginal heading '
                      '“Complaints against service providers.” shall be substituted;')
    assert ops == [{"op": "SUBSTITUTE_NODE", "target": "s.217/heading", "block": "Complaints against service providers."}]


def test_last_occurrence_and_heading():
    got = run({"op": "INSERT_WORDS", "target": "art.15", "position": "after", "anchor": "wells", "text": "and tanks",
               "last": True})
    assert "the use of wells." in got and "applies to wells and tanks." in got
    assert run({"op": "SUBSTITUTE_NODE", "target": "art.15/heading", "block": "New heading."}).startswith("# 15. New heading.\n")


def test_provisos_inside_explanations():
    """s.29A(j): contract 2 nests nothing under an Explanation, so "in Explanation I, for the proviso" finds the
    first proviso after it, and the proviso's own list (A), (B) goes with it."""
    text = ("# 29A. Persons not eligible.\n\nA person shall not be eligible—\n"
            "- (j) has a connected person.\n"
            "  - *Explanation*.—For the purposes of this clause, \"connected person\" means—\n"
            "  - (i) any promoter; or\n"
            "  - (ii) any holding company:\n"
            "    - *Provided that* nothing in clause (ii) shall apply to—\n"
            "    - (A) a scheduled bank; or\n"
            "    - (B) an asset reconstruction company.\n")
    got = apply({"part-ii/chapter-ii/section-029a.md": text}, [
        {"op": "INSERT_WORDS", "target": "s.29A(j)/explanation", "position": "after", "anchor": "Explanation", "text": "I"},
        {"op": "SUBSTITUTE_NODE", "target": "s.29A(j)/explanation/proviso", "block": "Provided that nothing applies."},
    ])["part-ii/chapter-ii/section-029a.md"]
    assert "*Explanation I*.—" in got and "    - *Provided that* nothing applies." in got
    assert "scheduled bank" not in got and "asset reconstruction" not in got


def test_roman_lists_hold_their_letters():
    """POCSO (Amendment) Act, 2019, s. 4: "(I) in clause (j),— (A) ... (C) after sub-clause (iii)": (A) to (C) are
    inside (I), not its siblings; and a quoted block closed mid-line lets "(II)" start the next instruction."""
    from baseline import baseline
    ops, misses = baseline('In section 5 of the principal Act,—\n(I) in clause (j),—\n'
                           '(A) in sub-clause (i), the word "or" occurring at the end shall be omitted;\n'
                           '(C) after sub-clause (iii), the following sub-clause shall be inserted, namely:—\n'
                           '"(iv) causes death of the child; or";\n(II) in clause (s), for the words "violence", the '
                           'words "violence or during any natural calamity" shall be substituted.')
    assert not misses
    assert [(o["op"], o["target"]) for o in ops] == [
        ("OMIT_WORDS", "s.5(j)(i)"), ("INSERT_NODE", "s.5(j)(iii)"), ("SUBSTITUTE_WORDS", "s.5(s)")]


PROVISOS = """# 22. Protection.

- (4) No law shall authorise detention—
  - (a) unless an Advisory Board has reported:
  - *Provided that* nothing in this sub-clause applies; or
  - (b) unless the person is detained under a law.
- (5) When any person is detained—
  - *Provided that* nothing shall apply to—
  - (A) a bank; or
  - (B) a company.
- (6) More.
"""


def test_the_executor_refuses_rather_than_guesses():
    """notes/audit-2026-11-24.md, E1 to E25: each of these applied a wrong edit without an error, or refused a
    right one."""
    law = {"part-iii/article-022.md": PROVISOS}
    one = lambda op: apply(law, [op])["part-iii/article-022.md"]  # noqa: E731
    got = one({"op": "OMIT_NODE", "target": "art.22(4)/proviso"})  # E1: a proviso to (a) printed before (b)
    assert "(b) unless the person" in got and "nothing in this sub-clause" not in got
    got = one({"op": "INSERT_NODE", "target": "art.22(5)/proviso", "position": "after", "block": "Provided further that x."})
    assert got.index("(B) a company.") < got.index("*Provided further that* x.") < got.index("(6)")  # E13
    got = one({"op": "INSERT_WORDS", "target": "art.22(5)(A)", "position": "after", "anchor": "bank", "text": ", a fund"})
    assert "a bank, a fund; or" in got  # E8
    assert "a bank or" not in one({"op": "OMIT_WORDS", "target": "art.22(5)(A)", "text": "; or"})  # E15
    for bad in ({"op": "INSERT_WORDS", "target": "art.22(6)", "position": "after", "anchor": "More", "text": "x",
                 "to": "y"},  # E10: "to" isn't an INSERT_WORDS field
                {"op": "OMIT_WORDS", "target": "art.22", "text": "a", "every": True, "last": True},  # E20
                {"op": "OMIT_WORDS", "target": "art.22", "text": "a", "every": "false"},
                {"op": "SUBSTITUTE_WORDS", "target": "art.22", "old": "", "new": "x"},
                {"op": "SUBSTITUTE_WORDS", "target": "art.22(6)", "old": "More", "new": "x\n- (7) y"},
                {"op": "OMIT_NODE", "target": "art.22/proviso1"},  # E24
                {"op": "RENUMBER", "target": "art.22/heading", "label": "7"}):  # E14
        with pytest.raises(EditError):
            one(bad)
    with pytest.raises(EditError, match="2 provisions"):  # E6: a Schedule that repeats its labels
        apply({"schedule-2.md": "# SECOND SCHEDULE\n\n- (a) one\n- PART B\n- (a) two\n"},
              [{"op": "OMIT_NODE", "target": "sch.2(a)"}])
    with pytest.raises(EditError, match="not found"):  # E7: (10)'s proviso isn't (1)'s
        apply({"section-005.md": "# 5. X.\n\n- (1) One.\n- (10) Ten.\n  - *Provided that* y.\n"},
              [{"op": "OMIT_NODE", "target": "s.5(1)/proviso"}])
    assert structure("12. Salaries.—\n(1) There shall be paid.\n(2) More.", schedule=True) == [  # E9
        (0, "12. Salaries.—"), (1, "(1) There shall be paid."), (1, "(2) More.")]


def test_whole_files_by_id():
    """E4, E5, E25: Chapters named by their numeral, no second section with an ID that exists, articles as files."""
    files = {"part-ii/chapter-iii/section-054.md": "# 54. X.\n\n- (1) Text.\n", "part-ii/chapter-iii/README.md": "# CHAPTER III\n\nX\n",
             "part-ii/chapter-iv/README.md": "# CHAPTER IV\n\nY\n",
             "part-ii/chapter-iv/section-060.md": "# 60. Y.\n\nText.\n", "part-ii/chapter-iv/section-054a.md": "# 54A. Z.\n\nT.\n"}
    got = apply(files, [{"op": "INSERT_NODE", "target": "s.60", "position": "after", "block": "CHAPTER V TITLE\n61. New.—Text."}])
    assert "part-ii/chapter-v/README.md" in got
    for block in ("CHAPTER IV TITLE\n61. New.—Text.", "54A. Again.—Text."):
        with pytest.raises(EditError, match="exists already"):
            apply(files, [{"op": "INSERT_NODE", "target": "s.54", "position": "after", "block": block}])
    law = {"part-iii/article-015.md": ART, "part-iii/article-031.md": "# 31. Property.\n\nText.\n"}
    assert "part-iii/article-031.md" not in apply(law, [{"op": "OMIT_NODE", "target": "art.31"}])
    got = apply(law, [{"op": "INSERT_NODE", "target": "art.15", "position": "after", "block": "15A. New.—Text."}])
    assert got["part-iii/article-015a.md"] == "# 15A. New.\n\nText.\n"


def test_baseline_misses_rather_than_half_applies():
    """E2, E3, E11, E16, E17."""
    from baseline import baseline
    ops, misses = baseline("In section 5 of the principal Act, clauses (a) to (d) shall be omitted.")
    assert [o["target"] for o in ops] == ["s.5(a)", "s.5(b)", "s.5(c)", "s.5(d)"] and not misses
    ops, misses = baseline("In section 5 of the principal Act, clauses (2A) to (2D) shall be omitted.")
    assert not ops and misses
    ops, _ = baseline("In section 5 of the principal Act, after clause (z), the following clauses shall be inserted, "
                      "namely:—\n“(za) “creditor” has the meaning given to the term “creditor”;\n"
                      "(zb) “debt” means a liability.”.")
    assert ops[0]["block"].endswith("(zb) “debt” means a liability.")
    ops, _ = baseline("In the Fourth Schedule, in item 2 relating to section 11, for the word “x”, the word “y” "
                      "shall be substituted.")
    assert ops[0]["target"] == "sch.4(2)"
    ops, _ = baseline("In section 5, after the words ‘‘in clause (a)’’, the words ‘‘or (b)’’ shall be inserted.")
    assert ops == [{"op": "INSERT_WORDS", "target": "s.5", "position": "after", "anchor": "in clause (a)", "text": "or (b)"}]
    ops, _ = baseline('In section 5 of the principal Act,—\n(h) in clause (8),—\n(A) for the word "a", the word "b" '
                      'shall be substituted;\n(i) in clause (9), for the word "c", the word "d" shall be substituted.')
    assert [o["target"] for o in ops] == ["s.5(8)", "s.5(9)"]


def test_the_harness_scores_the_law_produced():
    """M2.md T24: exact match on the law after the output, validity, unintended changes, and edit F1 beside them."""
    from run import main, score
    gold = [{"op": "SUBSTITUTE_WORDS", "target": "art.15(2)(a)", "old": "shops", "new": "markets"}]
    item = {"output": json.dumps(gold), "before": F, "after": apply(F, gold)}
    assert score(item, json.dumps(gold)) == {"valid": True, "exact": True, "words": True, "unintended": False,
                                             "ops": 1, "gold_ops": 1, "matched": 1}
    loose = score(item, json.dumps([{**gold[0], "target": "art.15"}]))  # the same law by another op: exact, not F1
    assert loose["exact"] and loose["matched"] == 0
    drift = score(item, json.dumps(gold + [{"op": "SUBSTITUTE_WORDS", "target": "art.15(1)", "old": "citizen", "new": "person"}]))
    assert drift["valid"] and drift["unintended"] and not drift["exact"]
    for bad in ("not JSON", '{"op": "OMIT_NODE"}', json.dumps([{**gold[0], "target": "art.99"}])):
        assert score(item, bad)["valid"] is False and score(item, bad)["unintended"] is None
    rows = main(["regex", str(ROOT / "history" / "constitution.yaml"), str(ROOT / "history" / "rti-act.yaml"), "--runs", "1"])
    assert len(rows) == 16 and sum(r["exact"] for r in rows) == 12  # as engine/replay.py has it
