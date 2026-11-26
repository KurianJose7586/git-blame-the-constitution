"""The evaluation harness (M2.md T24): any system, amending text in and operations out, scored on the law it
produces (decision 4).

    uv run eval/run.py regex out/examples/*.jsonl history/*.yaml --by law,silver

A system is `regex` (engine/baseline.py) or FILE.py:FUNCTION, a function from an item's input to its output, the
JSON of engine/ops.schema.json. Items are model/examples.py's records, or the amending provisions of a hand-written
history (M0), whose after-text nobody derived from the baseline but which have no gold operations. Per stratum
(--by, item fields) it prints, as a table for notes/results.md:

    exact       the files the item carries, after the output, equal the gold after-text exactly (the primary
                metric: no whitespace or punctuation is forgiven)
    words       ... have the same words, as engine/replay.py's lowest level; for reading the misses, not a score
    valid       the output parses and every operation applies
    unintended  a line the gold leaves alone is changed or removed, of the valid outputs
    edit F1     the output's operations against the gold's, targets made canonical; items with gold operations only
    same        all --runs outputs are identical
    s/item      the system's time on the first run
"""
import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "engine"), str(ROOT / "model")]
from baseline import baseline  # noqa: E402
from examples import canonical, example, touchable  # noqa: E402
from ops import EditError, apply_one  # noqa: E402
from replay import norm, steps  # noqa: E402


def regex(source):
    """engine/baseline.py as a system: the provision's text, after its heading's line, in."""
    return json.dumps(baseline(source.split("\n---\n", 1)[0].split("\n", 1)[1])[0], ensure_ascii=False)


def load_system(spec):
    if spec == "regex":
        return regex
    path, _, name = spec.rpartition(":")
    module_spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return getattr(module, name)


def items(path):
    if not path.endswith(".yaml"):
        yield from (json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines())
        return
    history = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for act, sec, before, after in steps(history):
        source, _, targets, _, _ = example(before, "", sec["text"], [])  # no heading: M0 recorded none
        before, after = touchable(before, after, targets)
        yield {"law": history["law"], "act": act["act"], "section": sec.get("section"), "input": source,
               "output": None, "targets": targets, "before": before, "after": after}


def applied(files, output):
    """The law after the output, and its operations with canonical targets; EditError (a ValueError) if invalid."""
    ops = json.loads(output)
    if not isinstance(ops, list) or not all(isinstance(op, dict) and isinstance(op.get("target"), str) for op in ops):
        raise EditError("not a list of operations")
    done = []
    for op in ops:
        after = apply_one(files, op)
        done.append({**op, "target": canonical(files, op["target"])})
        files = after
    return files, done


def kept(before, after):
    """{path: indexes of the lines of before that survive in after}."""
    def survive(a, b):
        return {i for m in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks() for i in range(m.a, m.a + m.size)}
    return {p: survive(t.split("\n"), after[p].split("\n") if p in after else []) for p, t in before.items()}


def key(op):
    return json.dumps(op, sort_keys=True, ensure_ascii=False)


def score(item, output):
    """One output against one item."""
    gold = item["after"]
    try:
        got, ops = applied(item["before"], output)
    except ValueError:
        got = None
        try:
            ops = [op for op in json.loads(output) if isinstance(op, dict)]
        except (ValueError, TypeError):
            ops = []
    same_files = got is not None and got.keys() == gold.keys()
    gold_ops = None if item["output"] is None else json.loads(item["output"])
    return {"valid": got is not None,
            "exact": same_files and all(got[p] == gold[p] for p in gold),
            "words": same_files and all(norm(got[p], "words") == norm(gold[p], "words") for p in gold),
            # ponytail: by line; a wrong word in a line the gold also changes fails exact, not this
            "unintended": None if got is None else any(g - s for g, s in zip(
                kept(item["before"], gold).values(), kept(item["before"], got).values())),
            "ops": len(ops), "gold_ops": None if gold_ops is None else len(gold_ops),
            "matched": None if gold_ops is None else sum((Counter(map(key, ops)) & Counter(map(key, gold_ops))).values())}


def table(rows, by):
    groups = defaultdict(list)
    for r in rows:
        groups[" ".join(str(r["item"].get(f)) for f in by)].append(r)
    groups["all"] = rows

    def pct(rs, k):
        rs = [r for r in rs if r[k] is not None]
        return f"{100 * sum(r[k] for r in rs) / len(rs):.0f}%" if rs else "n/a"

    lines = [f"| {', '.join(by)} | items | exact | words | valid | unintended | edit F1 | same | s/item |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, rs in groups.items():
        scored = [r for r in rs if r["gold_ops"] is not None]
        p = sum(r["matched"] for r in scored) / max(sum(r["ops"] for r in scored), 1)
        rc = sum(r["matched"] for r in scored) / max(sum(r["gold_ops"] for r in scored), 1)
        f1 = "n/a" if not scored else f"{200 * p * rc / (p + rc):.0f}%" if p + rc else "0%"
        lines.append(f"| {name} | {len(rs)} | {pct(rs, 'exact')} | {pct(rs, 'words')} | {pct(rs, 'valid')} | "
                     f"{pct(rs, 'unintended')} | {f1} | {pct(rs, 'same')} | {sum(r['seconds'] for r in rs) / len(rs):.3f} |")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("system")
    parser.add_argument("items", nargs="+")
    parser.add_argument("--by", default="law", help="item fields to group by, comma-separated")
    parser.add_argument("--runs", type=int, default=5, help="runs per item, for determinism")
    args = parser.parse_args(argv)
    system, rows = load_system(args.system), []
    for path in args.items:
        for item in items(path):
            start = time.perf_counter()
            outputs = [system(item["input"])]
            seconds = time.perf_counter() - start
            outputs += [system(item["input"]) for _ in range(args.runs - 1)]
            rows.append({"item": item, **score(item, outputs[0]), "same": len(set(outputs)) == 1, "seconds": seconds})
    print(table(rows, args.by.split(",")))
    return rows


if __name__ == "__main__":
    main()
