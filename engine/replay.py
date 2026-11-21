"""Replay a law's hand-written history through the baseline and the executor (KICKOFF.md T17).

For each amending provision with text: turn the text into operations, apply them to the law as it stood before,
and compare with the history's own text after. Matches are graded: exact, equal after normalising quotes and
spaces ("quotes"), or the same words ("words").

    uv run engine/replay.py history/constitution.yaml history/rti-act.yaml
"""
import re
import sys
from pathlib import Path

import yaml

from baseline import baseline
from ops import EditError, apply

LEVELS = ("exact", "quotes", "words")


def norm(text, level):
    if level == "exact":
        return text
    text = " ".join(text.translate(str.maketrans("“”‘’", "\"\"''")).split())
    return text if level == "quotes" else " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def replay(history_path):
    history = yaml.safe_load(Path(history_path).read_text(encoding="utf-8"))
    files, results = {}, []
    for n, act in enumerate(history["amendments"]):
        for sec in act["sections"]:
            after = {**files, **{p: t if t.endswith("\n") else t + "\n" for p, t in sec["files"].items() if t is not None}}
            if n and sec.get("text"):  # the first entry is the Act itself, not an amendment
                ops, misses = baseline(sec["text"])
                try:
                    got, error = apply(files, ops), None
                except EditError as e:
                    got, error = files, str(e)
                match = next((lv for lv in LEVELS if all(norm(got[p], lv) == norm(after[p], lv) for p in sec["files"])), None)
                results.append({"amendment": act["act"] + (f", s. {sec['section']}" if sec.get("section") else ""),
                                "ops": ops, "misses": misses, "error": error, "match": match})
            files = after
    return results


if __name__ == "__main__":
    total = []
    for path in sys.argv[1:]:
        for r in replay(path):
            total.append(r)
            outcome = r["match"] or ("error: " + r["error"] if r["error"] else "no match")
            print(f"{outcome:<10.200} {len(r['ops'])} ops  {r['amendment']}" + (f"  (not understood: {r['misses']})" if r["misses"] else ""))
    covered = sum(not r["misses"] and bool(r["ops"]) for r in total)
    counts = {lv: sum(LEVELS.index(r["match"]) <= LEVELS.index(lv) for r in total if r["match"]) for lv in LEVELS}
    print(f"\n{len(total)} amending provisions; baseline understood {covered}; "
          + ", ".join(f"{lv} match {c}" for lv, c in counts.items()))
