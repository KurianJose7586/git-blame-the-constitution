"""Export a law repository to the reader's JSON (KICKOFF.md, contract 4), and refresh laws.json beside it.

    uv run publish/export.py out/constitution reader/data/constitution.json
"""
import json
import re
import sys
from pathlib import Path

from build_repo import git


def blame(repo, path):
    """(commit sha, line) for each line of the file at HEAD."""
    sha = None
    for line in git(repo, "blame", "--porcelain", "HEAD", "--", path).split("\n"):
        if line.startswith("\t"):
            yield sha, line[1:]
        elif re.match(r"[0-9a-f]{40} ", line):
            sha = line[:40]


def parse(message):
    # build_repo.py writes: subject, then the amending text (optional), then one paragraph of trailers.
    paras = message.strip().split("\n\n")
    trailers = dict(line.split(": ", 1) for line in paras[-1].split("\n"))
    return trailers, "\n\n".join(paras[1:-1]) or None


def export(repo, out):
    repo, out = Path(repo), Path(out)
    readme = (repo / "README.md").read_text(encoding="utf-8")
    commits, versions = [], {}
    for record in git(repo, "log", "--reverse", "--format=%H%x00%B%x1e").split("\x1e"):
        if not record.strip():
            continue
        sha, message = record.strip().split("\x00")
        t, text = parse(message)
        commits.append({
            "sha": sha, "act": t["Amending-Act"], "instrument": t.get("Instrument"),
            "section": t.get("Section"), "gazette": t.get("Gazette"),
            "enacted": t["Enacted"], "in_force": None if t["In-Force"] == "unknown" else t["In-Force"],
            "retrospective": t["Retrospective"] == "yes", "source": t["Source"], "text": text,
        })
        for line in git(repo, "diff-tree", "--root", "--no-commit-id", "-r", "--name-status", sha).splitlines():
            status, path = line.split("\t")
            if path.endswith(".md") and path != "README.md":
                body = None if status == "D" else git(repo, "show", f"{sha}:{path}")
                versions.setdefault(path, []).append({"commit": len(commits) - 1, "text": body})

    # The reader picks "the latest version in force on D". That is only right while each file's
    # in-force dates run in commit order (unknown counts as last); otherwise it needs M1's replay.
    for path, vs in versions.items():
        dates = [commits[v["commit"]]["in_force"] or "9999-12-31" for v in vs]
        if dates != sorted(dates):
            sys.exit(f"{path}: in-force dates are out of commit order, so 'as in force' needs the M1 replay")

    index = {c["sha"]: i for i, c in enumerate(commits)}
    files = [
        {"path": path, "versions": vs,
         "blame": [index[sha] for sha, _ in blame(repo, path)] if vs[-1]["text"] is not None else []}
        for path, vs in sorted(versions.items())
    ]
    data = {
        "version": 1,
        "law": out.stem,
        "title": readme.split("\n", 1)[0].removeprefix("# "),
        "official": re.findall(r"https?://\S+", readme)[-1],
        "commits": commits,
        "files": files,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    laws = [{"law": p.stem, "title": json.loads(p.read_text(encoding="utf-8"))["title"]}
            for p in sorted(out.parent.glob("*.json")) if p.name != "laws.json"]
    (out.parent / "laws.json").write_text(json.dumps(laws, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(export(sys.argv[1], sys.argv[2]))
