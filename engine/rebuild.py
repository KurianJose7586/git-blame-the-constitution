"""A law's history, rebuilt backwards from its consolidated text's footnotes. Silver data: local only.

    uv run engine/rebuild.py out/coi.txt out/constitution-silver.yaml
    uv run publish/build_repo.py out/constitution-silver.yaml out/constitution-silver

Each footnote that records a change is undone, newest first, on the text engine/constitution.py parsed: an
insertion comes out, and a substitution or an omission puts back the words its footnote quotes. Where the footnote
doesn't quote the earlier text ("Subs. ..., for cl. (2)"), a bracketed placeholder stands in for it, so blame is
still right where the old words aren't known. Omitted articles, clauses and Parts come back the same way. The
output is a history file in contract 1, one commit per section of each instrument.

Silver, not gold: the footnotes' quotes are sometimes wrong ("Unity of the Nation"), commits are placed at
in-force dates because the footnotes give no enactment dates, and a placeholder isn't law.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath

import yaml

import constitution as C
from footnotes import parse as read_note

ROOT = Path(__file__).resolve().parents[1]
CHANGES = {"inserted", "added", "substituted", "omitted", "relettered", "renumbered", "amended"}
LEAD = re.compile(r"^(?:\d+[A-Z]*\.\s|\(\w+\)\s)")  # a number or label a placeholder keeps: "239. ", "(2) "
COMPOUND = re.compile(r"(?:\band\s+(?:further\s+|subsequently\s+|then\s+)?|This amendment was\s+|subsequently\s+)"
                      r"(?=(?:subs|ins|omitted|re-?numbered|re-?lettered|added)\b)", re.I)
OMITTED_ARTICLE = re.compile(r"^\W*\[?(\d+)([A-Z]*)\.\s*\[?(.*?)\.?\]?\.?\s*—\s*(.*)$", re.S)


def placeholder(note):
    section = f", s. {note['section']}" if note.get("section") else ""
    return f"[before {note['instrument']}{section}: not quoted in the footnote]"


class Text:
    """The law as lines with stable IDs, each with its source (markers as tokens), so changes can be undone."""

    def __init__(self, files, trail):
        self.order = {path: [(path, n) for n in range(1, text.count("\n") + 1)] for path, text in files.items()}
        self.shown = {(path, n): line for path, text in files.items() for n, line in enumerate(text.split("\n")[:-1], 1)}
        self.src = {(path, n): source for path, n, source in trail if path}
        self.added = 0

    def files(self):
        out = {}
        for path, uids in self.order.items():
            lines = [self.shown[uid] for uid in uids]
            while lines and not lines[-1]:
                lines.pop()
            if any(lines):
                out[path] = "\n".join(lines) + "\n"
        return out

    def alive(self, uid):
        return uid in self.shown and any(uid in uids for uids in self.order.values())

    def set(self, uid, source):
        """A new source for a line, shown in the line's old format ("  - ", "# ", "*Provided that*")."""
        old = self.shown[uid]
        prefix = re.match(r"^(?:# |\s*- )?", old)[0]
        body = " ".join(C.OMISSION.sub("", C.flat(source)).split())
        if old[len(prefix):].startswith("*"):
            body = re.sub(r"^(Provided(?: further| also)? that|Explanation)", r"*\1*", body)
        self.src[uid], self.shown[uid] = source, prefix + body

    def add(self, path, after, prefix, source):
        """A new line after the line `after` (at the end if it isn't in the file)."""
        self.added += 1
        uid = ("+", self.added)
        uids = self.order.setdefault(path, [])
        uids.insert(uids.index(after) + 1 if after in uids else len(uids), uid)
        self.shown[uid] = prefix
        self.set(uid, source)
        return uid

    def drop(self, uid):
        for uids in self.order.values():
            if uid in uids:
                uids.remove(uid)


def brackets(text, fid, lines):
    """Each of fid's bracket pairs on these lines: (first line, opening token, last line, closing token or None).
    One note can mark two brackets ("7[Puducherry]" twice on a page), so each pair is undone on its own."""
    pairs, open_at = [], None
    for uid in lines:
        for m in C.TOKEN.finditer(text.src[uid]):
            if m[2] == fid and m[1] == C.OPEN:
                open_at = (uid, m)
            elif m[2] == fid and m[1] == C.CLOSE and open_at:
                pairs.append((*open_at, uid, m))
                open_at = None
    if open_at:  # it closes on a line with no file
        pairs.append((*open_at, lines[-1], None))
    return pairs


def between(lines, first, last):
    return lines[lines.index(first) + 1:lines.index(last) + 1] if first != last else []


def undo(text, fid, note, covers, aside):
    """Undo one footnote's change in place; returns what happened, for the report."""
    kind, old = note["kind"], note.get("old")
    lines = [tuple(c) for c in covers if len(c) == 2 and text.alive(tuple(c))]
    labels = [c[0] for c in covers if len(c) == 1]
    if kind in ("inserted", "added"):
        for label in labels:  # inserted, then omitted later: the rebuilt unit goes again
            for path in aside.pop(label, []):
                text.order.pop(path, None)
        lines += [uid for uid in aside.pop(("lines", fid), []) if text.alive(uid)]
        return remove(text, fid, lines) if lines else "removed" if labels else "lost"
    points = [(uid, m) for uid in lines for m in C.TOKEN.finditer(text.src[uid]) if m[2] == fid and m[1] == C.POINT]
    pairs = brackets(text, fid, lines)
    if kind == "omitted" and points:  # "the Governor 2*** of a State": the words go back where the stars are
        for uid, m in reversed(points):
            source = text.src[uid]
            rest = re.sub(r"^\s*(?:\*\s*)+", " ", source[m.end():])
            text.set(uid, f"{source[:m.start()]} {C.OPEN}{fid}{C.END}{old or placeholder(note)}{C.CLOSE}{fid}{C.END}{rest}")
    elif pairs:
        for first, start, last, end in reversed(pairs):
            if not text.alive(first) or not text.alive(last):
                continue
            stop = end.start() if end else len(text.src[last])
            inside = C.flat(text.src[first][start.end():stop if first == last else None])
            keep = "" if old or not LEAD.match(inside) else LEAD.match(inside)[0]
            tail = text.src[last][stop:]  # the closing token stays, for the other half of a compound note
            text.set(first, text.src[first][:start.end()] + keep + (old or placeholder(note)) + tail)
            for uid in between(lines, first, last):
                text.drop(uid)
    elif kind == "omitted" and labels:
        return restore(text, fid, note, labels, aside)
    else:
        return "lost"  # a superscript reference, or a line a later change already rewrote
    return "restored" if old else "placeholder"


def remove(text, fid, lines):
    """Undo an insertion: a file whose heading is inside the brackets goes; so do lines wholly inside them."""
    for path in dict.fromkeys(uid[0] for uid in lines):
        if (path, 1) in lines:
            text.order.pop(path, None)
    inside = {uid for first, _, last, _ in brackets(text, fid, lines) for uid in between(lines, first, last)[:-1]}
    for uid in lines:
        if not text.alive(uid):
            continue
        if uid in inside:
            text.drop(uid)
            continue
        source, kept, at = text.src[uid], "", 0
        marks = [m[1] for m in C.TOKEN.finditer(source) if m[2] == fid and m[1] != C.POINT]
        depth = 0 if marks and marks[0] == C.OPEN else 1  # a line that starts inside a bracket opened above
        for m in C.TOKEN.finditer(source):
            if m[2] != fid or m[1] == C.POINT:
                continue
            if m[1] == C.OPEN:
                kept += source[at:m.start()] if depth == 0 else ""
                depth += 1
            elif depth:
                depth -= 1
            at = m.end()
        kept += source[at:] if depth == 0 else ""
        if C.flat(kept).strip(" .,;:"):
            text.set(uid, kept)
        else:
            text.drop(uid)
    return "removed"


def restore(text, fid, note, labels, aside):
    """Undo the omission of something with no file: a clause ("(f)* * * * *") or a Part."""
    done = "lost"
    for label in labels:
        for source, path, after in aside.get(("unit", label), []):
            if fid not in {f for _, f in C.TOKEN.findall(source)}:
                continue
            words = note.get("old") or placeholder(note)
            if label.startswith("PART"):  # "PART VII" / "[The States in Part B of the First Schedule]."
                title = re.sub(r"^\W*PART\s+\w+\s*", "", C.flat(source)).strip("[]. ")
                folder = f"part-{label.split()[1].lower()}"
                text.add(f"{folder}/README.md", None, "# ", label)
                text.add(f"{folder}/README.md", None, "", "")
                text.add(f"{folder}/README.md", None, "", title or words)
                aside.setdefault(label, []).append(f"{folder}/README.md")
            elif m := C.LABEL.match(C.flat(source)):
                prefix = re.match(r"^\s*- ", text.shown.get(after, "")) if after else None
                uid = text.add(path, after, prefix[0] if prefix else "- ", f"{C.OPEN}{fid}{C.END}{m[0]} {words}{C.CLOSE}{fid}{C.END}")
                aside.setdefault(("lines", fid), []).append(uid)
            done = "restored" if note.get("old") else "placeholder"
    return done


def unit_file(label, source, path):
    """An omitted article, rebuilt as a file next to the article before it: (path, heading source, its note)."""
    m = OMITTED_ARTICLE.match(C.flat(source))
    if not m or not path:
        return None
    number, letters, heading, body = m.groups()
    return (str(PurePosixPath(path).parent / f"article-{int(number):03d}{letters.lower()}.md"),
            f"{number}{letters}. {heading.strip('[] ')}.", body)


# --- The history ------------------------------------------------------------------------------------------

def events(provenance, trail):
    """Every change to undo: (id, note, covers, document position, nesting depth), and each footnote's enclosing
    footnotes: a change inside another's brackets was made after it, whatever the dates say."""
    depth, position, stack, parents = {}, {}, [], {}
    for n, (_, _, source) in enumerate(trail):
        for kind, fid in C.TOKEN.findall(source):
            position.setdefault(fid, n)
            if kind != C.CLOSE:
                parents.setdefault(fid, set()).update(f for f in stack if f != fid)
            if kind == C.OPEN:
                depth[fid] = len(stack)
                stack.append(fid)
            elif kind == C.CLOSE and fid in stack:
                stack.remove(fid)
    out, last_second = [], None
    for fid, note in provenance.items():
        # not changes to this text: one not in force ("shall stand substituted"), or one that applies only in some
        # States ("Paragraph 4 has been amended in its application to the State of Assam")
        if note["kind"] in CHANGES and note["instrument"] and not re.search(r"shall stand|amended (?:in|to) its application", note["text"]):
            out.append((fid, note, note["covers"], position.get(fid, 0), depth.get(fid, 0)))
            then = COMPOUND.split(note["text"], 1)
            second = read_note(then[1]) if len(then) > 1 else None
            if second and second["ibid"]:  # "and further subs. by s. 43, ibid.": the later instrument on this page
                second["instrument"] = last_second or note["instrument"]
            if second and second["kind"] in CHANGES and second["instrument"]:
                last_second = second["instrument"]
                out.append((f"{fid}/2", second, note["covers"], position.get(fid, 0), depth.get(fid, 0)))
    for n, (path, label, source) in enumerate(trail):  # omitted articles say so in their own text
        if path is None and label.startswith("art.") and OMITTED_ARTICLE.match(C.flat(source)):
            note = read_note(OMITTED_ARTICLE.match(C.flat(source))[4])
            if note["kind"] and note["instrument"]:
                out.append((f"text:{label}", note, [[label]], n, -1))
    return out, parents


def when(group, notes):
    """Where a group of changes goes in time: its in-force date, else its instrument's earliest, else its year."""
    instrument = group[0]
    dated = [n["wef"] for n in notes if n["wef"]]
    if dated:
        return date.fromisoformat(min(dated)), False
    year = re.search(r"\b(1[89]\d\d|20\d\d)\b", instrument)
    return date(int(year[1]) if year else 1950, 1, 1), True


def after_enclosing(order, groups, parents):
    """`order` (sorted by date) rearranged so a group comes after every group whose brackets enclose its changes.
    The 70th Amendment changed art. 239AA from 21 Dec 1991; the 69th, which inserted it, came in on 1 Feb 1992."""
    group_of = {e[0]: g for g, es in groups.items() for e in es}
    needs = {g: {group_of[p] for e in es for p in parents.get(e[0], ()) if p in group_of} - {g} for g, es in groups.items()}
    done, out, waiting = set(), [], list(order)
    while waiting:
        ready = next((w for w in waiting if needs[w[1]] <= done), waiting[0])  # a cycle: fall back to the date
        waiting.remove(ready)
        out.append(ready)
        done.add(ready[1])
    return out


def rebuild(files, provenance, trail, official):
    text = Text(files, trail)
    aside = {}  # ("unit", label) -> [(source, path of the line before, that line's ID)]; label -> rebuilt paths
    last_placed = None
    for path, number, source in trail:
        if path:
            last_placed = (path, number)
        else:
            aside.setdefault(("unit", number), []).append((source, last_placed[0] if last_placed else None, last_placed))

    groups, (changes, parents) = {}, events(provenance, trail)
    for event in changes:
        note = event[1]
        groups.setdefault((note["instrument"], note["section"]), []).append(event)
    placed = {}
    for instrument in {g[0] for g in groups}:
        all_notes = [e[1] for g, es in groups.items() if g[0] == instrument for e in es]
        placed[instrument] = when((instrument,), all_notes)
    order = []
    for group, es in groups.items():
        notes = [e[1] for e in es]
        own = any(n["wef"] for n in notes)
        day, guessed = when(group, notes) if own else placed[group[0]]
        section = group[1] or ""
        year = re.search(r"\b(1[89]\d\d|20\d\d)\b", group[0])  # same day: the later Act, then the inner change
        deepest = max(e[4] for e in es)
        order.append(((day, int(year[1]) if year else 0, deepest, group[0], int(re.match(r"\d*", section)[0] or 0),
                       section), group, not own))
    order = after_enclosing(sorted(order), groups, parents)

    report = {"undone": {}, "lost": [], "no_change": []}
    commits, latest = [], {}
    for n, ((day, *_), group, _) in enumerate(order):  # placed in order, never before the commit before it
        latest[group] = max(day, latest[order[n - 1][1]]) if n else day
    for (day, *_), group, guessed in reversed(order):
        before = text.files()
        for fid, note, covers, _, _ in sorted(groups[group], key=lambda e: (-e[4], -e[3])):
            if fid.startswith("text:"):
                label = fid[5:]
                source, path, _ = aside[("unit", label)][0]
                rebuilt = unit_file(label, source, path)
                if rebuilt:
                    new_path, heading, _ = rebuilt
                    text.add(new_path, None, "# ", heading)
                    text.add(new_path, None, "", "")
                    text.add(new_path, None, "", placeholder(note))
                    aside.setdefault(label, []).append(new_path)
                result = "placeholder" if rebuilt else "lost"
            else:
                result = undo(text, fid.split("/")[0], note, covers, aside)
            report["undone"][result] = report["undone"].get(result, 0) + 1
            if result == "lost":
                report["lost"].append(f"{fid}: {note['text'][:120]}")
        after = text.files()
        changed = {path: before.get(path) for path in set(before) | set(after) if before.get(path) != after.get(path)}
        if not changed:
            report["no_change"].append(f"{group[0]}, s. {group[1]}")
            continue
        notes = [e[1] for e in groups[group]]
        commits.append({"act": group[0], "placed": latest[group], "section": group[1],
                        "in_force": None if guessed else day,
                        "retrospective": any(n["retrospective"] for n in notes) or None,
                        "footnotes": [n["text"] for n in notes], "files": changed})
    commits.reverse()

    amendments = [{"act": "The Constitution of India", "enacted": date(1949, 11, 26), "source": official,
                   "sections": [{"section": None, "in_force": date(1950, 1, 26), "files": text.files()}]}]
    for c in commits:
        sec = {k: c[k] for k in ("section", "in_force", "retrospective", "footnotes", "files") if c[k] is not None}
        sec.setdefault("section", None)
        if amendments[-1]["act"] == c["act"] and amendments[-1].get("placed"):
            amendments[-1]["sections"].append(sec)
        else:
            amendments.append({"act": c["act"], "enacted": None, "placed": c["placed"], "source": official,
                               "sections": [sec]})
    report["commits"] = len(commits)
    return amendments, report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pages = Path(sys.argv[1]).read_text(encoding="utf-8").split("\f")
    files, provenance, _, trail = C.parse(pages)
    gold = yaml.safe_load((ROOT / "history" / "constitution.yaml").read_text(encoding="utf-8"))
    amendments, report = rebuild(files, provenance, trail, gold["official"])
    history = {"law": "constitution", "title": "The Constitution of India", "official": gold["official"],
               "note": "Silver: rebuilt from the consolidated text's footnotes by engine/rebuild.py. Commits are "
                       "placed at in-force dates; text in square brackets stands in for words no footnote quotes.",
               "amendments": amendments}
    yaml.add_representer(str, lambda d, v: d.represent_scalar(  # files as readable blocks
        "tag:yaml.org,2002:str", v, style="|" if "\n" in v else None), Dumper=yaml.SafeDumper)
    out = Path(sys.argv[2])
    out.write_text(yaml.safe_dump(history, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    out.with_suffix(".report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{report['commits']} commits; undone: {report['undone']}; no change: {len(report['no_change'])}")
