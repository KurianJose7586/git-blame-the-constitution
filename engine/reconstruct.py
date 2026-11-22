"""Reconstruction (KICKOFF.md T18): an Act as gazetted, then each amending Act in turn, compared on the way with
official consolidations.

    uv run engine/reconstruct.py out/ibc/code-2016 out/ibc/replay \\
        out/ibc/g/2018-01-18-amendment-act-2017.txt out/ibc/g/2018-08-17-second-amendment-act-2018.txt \\
        =out/ibc/consolidated-2018-08-17.txt ...

The first argument is the Act parsed by engine/constitution.py --act, the second a folder for the result. Then, in
order, amending Acts (text from ingest/pdf.py --gazette) and, prefixed with "=", consolidated texts to compare with
at that point. Each amending provision goes through the regex baseline and the executor; a consolidated text is
compared word for word, file by file. The result's files and report.json go in the output folder.
"""
import difflib
import json
import re
import sys
from pathlib import Path

from baseline import baseline
from ops import FILE_ID, EditError, apply_one, file_id

SKIP = re.compile(r"Short title|Repeal and savings|^Ord\.|Validation|of Act \d+ of \d{4}")
LABEL = r"\((?:\d+[A-Z]*|[a-z]{1,6}|[A-Z])\)\s"


def provisions(text):
    """An amending Act's sections as (number, heading, instructions), each instruction and each provision of a
    quoted block on a line of its own, as baseline() reads them. The short title, repeal and savings, and
    amendments of other Acts are left out."""
    text = text.replace("\f", "\n")
    out = []
    for line in text[text.lower().find("be it enacted"):].split("\n")[1:]:
        m = re.match(r"^(\d+)\.\s+(.*?)—(.*)$", line)
        if m and int(m[1]) == (int(out[-1][0]) + 1 if out else 1):
            out.append([m[1], m[2], [m[3]]])
        elif out:
            out[-1][2].append(line)
    kept = []
    for number, heading, lines in out:
        joined = " ".join(" ".join(lines).split())
        joined = re.sub(r"(?<=[;:—] )(\(\w{1,5}\))(?=[a-z])", r"\1 ", joined)  # "; (e)in clause (t)": a label glued on
        if SKIP.search(heading) or re.search(r"hereby repealed|such repeal", joined):
            continue
        # A label starts a line after "—", ":", ";", ".", "; and" or "; or", not after a comma: "sub-sections (6),
        # (6A)"; so do a proviso and an Explanation, and a quoted block after "namely:—".
        joined = re.sub(rf"(?<=[—:;.])\s+(?={LABEL})|(?:(?<=; and)|(?<=; or))\s+(?={LABEL})", "\n", joined)
        joined = re.sub(r"(?<=[—:;.])\s*(?=(?:Provided|Explanation)\b)", "\n", joined)
        joined = re.sub(r"(?<=—)\s*(?=[“\"'‘])", "\n", joined)
        joined = re.sub(r"(?<=[.;:—”\"'’])\s+(?=\d+-?[A-Z]+\.\s*[A-Z(])", "\n", joined)  # a new section inside a new Chapter
        kept.append((number, heading, joined))
    return kept


def load(folder):
    return {p.relative_to(folder).as_posix(): p.read_text(encoding="utf-8") for p in Path(folder).rglob("*.md")}


def in_order(files):
    """The files in document order: the preamble, sections by number with each Part's and Chapter's heading just
    before its first section, then the Schedules."""
    def key(path):
        name = path.rsplit("/", 1)[-1]
        if name == "preamble.md":
            return (0,)
        if m := re.fullmatch(r"schedule-(\d+)\.md", name):
            return (2, int(m[1]))
        if m := re.fullmatch(r"section-(\d+)([a-z]*)\.md", name):
            return (1, int(m[1]), m[2], 0)
        folder = path.rsplit("/", 1)[0] + "/"  # a README: before the first section in its folder
        first = min((key(p) for p in files if p.startswith(folder) and "section-" in p), default=(1, 10 ** 6, ""))
        return (1, *first[1:3], folder.count("/") - 10)
    return sorted(files, key=key)


def words(text):
    return re.findall(r"[a-z0-9]+", text.replace("—", " ").lower())


def consolidated(path):
    """A consolidated text's words, from its long title on: footnotes, footnote markers and page numbers out."""
    pages = Path(path).read_text(encoding="utf-8").split("\f")
    body = []
    for page in pages:
        lines = re.sub(r"^\s*\d+\s+(?=[(“\"A-Za-z])", "", page.strip()).split("\n")  # a page number on the first line
        cut = next((i for i, line in enumerate(lines) if re.match(r"^\s*1\s*[A-Z“\"‘]", line) and re.search(
            r"\bby Act\b|Act No\.|w\.r?\.e\.f|Subs\.|Ins\.|[Oo]mitted", " ".join(lines[i:i + 3]))), len(lines))
        body += [line for line in lines[:cut] if not re.fullmatch(r"\s*\d+\s*", line)]  # page numbers
    text = re.sub(r"\d+\s*(?=[\[*])", "", "\n".join(body))  # footnote markers: "1[", "2***"
    text = re.sub(r"\[?\(\w+\)\s*(?:\*\s*){3,}\]?", "", text)  # an omitted clause, "(g) * * *": law files leave it out
    return words(text[text.find("An Act to"):])


def compare(files, path):
    """Which law files' words appear, in order and with nothing missing or added, in the consolidated text. Words
    the consolidated text has between two files count against the file before."""
    ours, owner = [], []
    for p in in_order(files):
        found = words(re.sub(r"^#+ |^\s*- |\*", "", files[p], flags=re.M))
        ours += found
        owner += [p] * len(found)
    theirs, differ = consolidated(path), {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ours, theirs, autojunk=False).get_opcodes():
        if tag != "equal":
            for p in dict.fromkeys(owner[i1:i2] or owner[max(i1 - 1, 0):i1]):
                differ.setdefault(p, []).append(f"{' '.join(ours[i1:i2])[:80]!r} -> {' '.join(theirs[j1:j2])[:80]!r}")
    return {"files": len(files), "files_same": len(set(files) - set(differ)), "differ": differ}


def check(start, files, touched, path):
    """The replay against a consolidated text. A difference the Act as gazetted already had there is the
    consolidation's (spelling, typesetting, its own slips) or an amendment not applied; a new one is the replay's."""
    before, after = compare(start, path), compare(files, path)
    new = {p: [d for d in ds if d not in before["differ"].get(p, [])] for p, ds in after["differ"].items()}
    new = {p: ds for p, ds in new.items() if ds}
    amended = {p for p in files if file_id(p) in touched} | (set(files) - set(start))
    return {"consolidated": Path(path).name, "files": after["files"], "files_same": after["files_same"],
            "files_same_before": before["files_same"], "amended": len(amended),
            "amended_same": len(amended - set(after["differ"])),
            "amended_old_differences_only": len([p for p in amended if p in after["differ"] and p not in new]),
            "new_differences": new, "differ": after["differ"]}


def replay(base, steps):
    start = load(base)
    files, report, touched = dict(start), {"amendments": [], "checks": []}, set()
    for step in steps:
        if step.startswith("="):
            c = check(start, files, touched, step[1:])
            report["checks"].append(c)
            print(f"== {c['consolidated']}: {c['files_same']} of {c['files']} files match word for word "
                  f"({c['files_same_before']} before any amendment). Of the {c['amended']} files amended, "
                  f"{c['amended_same']} match, {c['amended_old_differences_only']} differ only where the Act as "
                  f"gazetted already did; {len(c['new_differences'])} files have new differences")
            continue
        act = Path(step).stem
        for number, heading, text in provisions(Path(step).read_text(encoding="utf-8")):
            ops, misses = baseline(text)
            touched |= {m[1] for op in ops if (m := FILE_ID.match(op["target"]))}
            touched |= {f"s.{n}" for n in re.findall(r"section (\d+[A-Z]*)", heading)}
            errors = []
            for op in ops:
                try:
                    files = apply_one(files, op)
                except EditError as e:
                    errors.append(str(e)[:300])
            outcome = "applied" if ops and not misses and not errors else "partly" if ops and len(errors) < len(ops) else "failed"
            report["amendments"].append({"act": act, "section": number, "heading": heading, "ops": len(ops),
                                         "misses": misses, "errors": errors, "outcome": outcome})
            print(f"  {act} s.{number:<3} {outcome:<8} {len(ops)} ops, {len(misses)} missed, {len(errors)} failed  {heading[:50]}")
    return files, report


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    out = Path(sys.argv[2])
    if out.exists():
        sys.exit(f"{out} exists; give a new folder")
    files, report = replay(sys.argv[1], sys.argv[3:])
    for p, text in files.items():
        (out / p).parent.mkdir(parents=True, exist_ok=True)
        (out / p).write_text(text, encoding="utf-8", newline="\n")
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {k: sum(a["outcome"] == k for a in report["amendments"]) for k in ("applied", "partly", "failed")}
    print(f"\n{len(report['amendments'])} amending provisions: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
