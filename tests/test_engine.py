"""M1 (KICKOFF.md T14, T16, T17): the executor, the regex baseline, and the replay of M0's hand-written history."""
import json
import random
import re
from pathlib import Path

import pytest
import yaml

from ops import OPS, EditError, apply, file_id, nodes, structure
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

    schema = json.loads((ROOT / "engine" / "ops.schema.json").read_text(encoding="utf-8"))
    assert {s["properties"]["op"]["const"]: set(s["required"]) - {"op"} for s in schema["items"]["oneOf"]} == {
        k: set(v) for k, v in OPS.items()}
    target = re.compile(schema["$defs"]["target"]["pattern"])
    assert all(target.match(op["target"]) for r in results for op in r["ops"])
