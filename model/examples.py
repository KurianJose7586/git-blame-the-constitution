"""The model's examples (M2.md T19, decision 2): an amending provision and the law it can touch in, its edit
operations out, as JSON per engine/ops.schema.json.

    uv run model/examples.py out/pocso/silver-2012 out/examples/pocso.jsonl steps...   # steps as for reconstruct.py

The law shown is every file the provision names outside its quotations ("In section 30", "the Fourth Schedule"),
each line after the ID a target would use, and the headings of the files either side. Targets in the output are
those IDs, so decoding can be held to them. A provision whose operations all applied is written out; it is silver
when the files it changed are still there at the next consolidation and have no new difference (decision 6; a
Schedule inserted and omitted before any consolidation is checked by none), and it round-trips when
its output, parsed back and applied, gives the law the replay did. Silver examples go to OUT.jsonl, the rest to
OUT.unchecked.jsonl, so nothing trains on an unchecked example by forgetting a flag. Each record also carries the
files it can touch, before and after, which eval/run.py scores a system's output against.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from ops import FILE_ID, ORDINALS, apply_one, file_id, find, nodes  # noqa: E402
from reconstruct import in_order, replay  # noqa: E402

NAMED = re.compile(rf"(?<![\w-])(?i:(section|article)s?)\s+((?:\d+[A-Z]*(?:,\s*|\s+(?:and|or|to)\s+)?)+)"  # not
                   rf"|\b((?i:{'|'.join(ORDINALS)}))\s+Schedule\b|\bthe\s+Schedule\b|\b(Preamble)\b")  # "sub-section 3"


def named(text):
    """The file IDs a provision names outside its quotations."""
    text = re.sub(r"“[^”]*”|\"[^\"]*\"|(?<!\w)[‘'][^’']*[’'](?!\w)", " ", text)  # "debtor’s" closes nothing
    ids = set()
    for m in NAMED.finditer(text):
        if m[1]:  # "sections 38 to 42" is every section between
            for a, b in re.findall(r"(\d+[A-Z]*)(?:\s+to\s+(\d+)\b)?", m[2]):
                ids |= {("s." if m[1].lower() == "section" else "art.") + n
                        for n in ([str(n) for n in range(int(a), int(b) + 1)] if b and a.isdigit() else [a])}
        else:
            ids.add("preamble" if m[4] else f"sch.{ORDINALS.index(m[3].lower()) + 1}" if m[3] else "sch.1")
    return ids


def touchable(before, after, targets):
    """The law an item carries for eval/run.py: the files shown and the files the gold changed, before and after.
    A target outside them can't be applied, so it counts against validity."""
    ids = {FILE_ID.match(t)[1] for t in targets}
    keep = {p for p in before if file_id(p) in ids} | {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
    return {p: before[p] for p in sorted(keep) if p in before}, {p: after[p] for p in sorted(keep) if p in after}


def shown(path, text):
    """[(ID, line)] of a file: a list item's ID, or the file's for its heading and opening words."""
    fid, ids = file_id(path), {first: suffix for suffix, first, _, _ in nodes(text)}
    return [(fid + ids.get(i, ""), line) for i, line in enumerate(text.split("\n")) if line.strip()]


def canonical(files, target):
    """The ID the law shown gives the provision a target finds ("s.18/explanation" -> "s.18(1)(g)/explanation")."""
    path, first, _, _ = find(files, target)
    if first is None or target.endswith("/heading"):
        return file_id(path) + ("/heading" if first is not None else "")
    return file_id(path) + next(s for s, f, _, _ in nodes(files[path]) if f == first)


def example(files, heading, text, ops):
    """(input, output, targets, shown, after) for one amending provision: shown is whether each op's target is in
    the law shown, or was made there by an op before it ("clause (a) shall be re-lettered as clause (ab) ... and
    before clause (ab) ..."); after is the law the output gives."""
    order = [p for p in in_order(list(files)) if file_id(p)]
    full = {p for p in order if file_id(p) in named(f"{heading}\n{text}")}
    near = {order[i + d] for i, p in enumerate(order) if p in full for d in (-1, 1) if 0 <= i + d < len(order)}
    law, targets = [], []
    for p in order:
        if p in full:
            law += shown(p, files[p])
            targets.append(file_id(p) + "/heading")
        elif p in near:
            law.append((file_id(p), files[p].split("\n")[0]))
    targets = list(dict.fromkeys([i for i, _ in law] + targets))
    out, now, seen = [], files, True
    for op in ops:  # each op's target is found in the law as the ops before it left it
        op = {**op, "target": canonical(now, op["target"])}
        path = find(now, op["target"])[0]
        old = {i for i, _ in shown(path, files[path])} if path in files else set()
        seen &= op["target"] in targets or (file_id(path) + "/heading" in targets and op["target"] not in old)
        now = apply_one(now, op)
        out.append(op)
    source = f"{heading}\n{text}\n---\n" + "\n".join(f"{i}\t{line}" for i, line in law)
    output = json.dumps(out, ensure_ascii=False)
    assert json.loads(output) == out  # the output parses back to the ops applied
    return source, output, targets, seen, now


def build(base, steps, law):
    kept = []
    _, report = replay(base, steps, kept)
    at_check = {k["check"]: k["after"] for k in kept}  # the law each check saw: after the last provision before it
    records = []
    for k in kept:
        if k["outcome"] != "applied":
            continue
        changed = {p for p in k["before"].keys() | k["after"].keys() if k["before"].get(p) != k["after"].get(p)}
        checks = report["checks"][k["check"]:]
        source, output, targets, seen, after = example(k["before"], k["heading"], k["text"], k["ops"])
        before_shown, after_shown = touchable(k["before"], k["after"], targets)
        records.append({"law": law, "act": k["act"], "section": k["section"],
                        "silver": bool(checks) and not changed & set(checks[0]["new_differences"])  # and still there:
                        and all(p in at_check[k["check"]] for p in changed if p in k["after"]),  # 2019's Eighth Schedule
                        "shown": seen, "round_trip": after == k["after"],
                        "input": source, "output": output, "targets": targets,
                        "before": before_shown, "after": after_shown})
    return records, len(kept)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    out = Path(sys.argv[2])
    records, provisions = build(sys.argv[1], sys.argv[3:], out.stem)
    out.parent.mkdir(parents=True, exist_ok=True)
    silver = [r for r in records if r["silver"]]
    for path, rs in ((out, silver), (out.with_suffix(".unchecked.jsonl"), [r for r in records if not r["silver"]])):
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), encoding="utf-8", newline="\n")
    print(f"\n{out}: {provisions} provisions, {len(records)} applied, {len(silver)} silver; of the silver, "
          f"{sum(r['shown'] for r in silver)} have every target in the law shown, "
          f"{sum(r['round_trip'] for r in silver)} round-trip; inputs up to "
          f"{max((len(r['input']) for r in silver), default=0):,} characters")
