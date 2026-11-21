"""Build a law's git repository from its history file (KICKOFF.md, contracts 1 and 3).

    uv run publish/build_repo.py history/constitution.yaml out/constitution
"""
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

import yaml

COMMITTER = ("KurianJose7586", "KurianJose7586@users.noreply.github.com")
AUTHOR_EMAIL = "amending-act@invalid"
IST = timezone(timedelta(hours=5, minutes=30))

README = """# {title}

The text of {title}, with one commit per section of each amending act. Commit trailers give the
amending act, its section, the Gazette reference, the date it was enacted and the date it came
into force. Commits follow the order of enactment, and tags such as `1977-12-31` mark the law as
published at the end of each year.

**Unofficial, and not legal advice.** The official text is at {official}
"""


def git(repo, *args, env=None, input=None):
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, input=input,
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout


def commit_date(enacted, n):
    # Git can't store dates before 1970: count seconds from the epoch instead, which keeps the order.
    if enacted.year < 1970:
        return f"@{n} +0000"
    return datetime(enacted.year, enacted.month, enacted.day, 12, tzinfo=IST).isoformat()


def message(act, sec):
    section = None if sec.get("section") is None else str(sec["section"])
    in_force = sec.get("in_force")
    trailers = {
        "Amending-Act": act["act"],
        "Section": section,
        "Gazette": act.get("gazette"),
        "Enacted": act["enacted"],
        "In-Force": in_force or "unknown",
        "Retrospective": "yes" if in_force and in_force < act["enacted"] else "no",
        "Source": act["source"],
    }
    subject = act["act"] + (f", s. {section}" if section else "")
    body = (sec.get("text") or "").strip()
    footer = "\n".join(f"{k}: {v}" for k, v in trailers.items() if v is not None)
    return "\n\n".join(p for p in (subject, body, footer) if p) + "\n"


def write(repo, path, text):
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts:
        sys.exit(f"bad path in history file: {path}")
    target = repo / p
    if text is None:
        target.unlink()
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def build(history_path, out):
    history = yaml.safe_load(Path(history_path).read_text(encoding="utf-8"))
    out = Path(out)
    if out.exists():
        sys.exit(f"{out} already exists; delete it first")
    out.mkdir(parents=True)
    git(out, "init", "-q", "-b", "main")
    git(out, "config", "core.autocrlf", "false")  # same bytes, so same hashes, on Windows and Linux
    write(out, "README.md", README.format(**history))

    commits = []  # (enacted, sha) in order
    for act in history["amendments"]:
        if commits and act["enacted"] < commits[-1][0]:
            sys.exit(f"{act['act']}: amendments must be in order of enactment")
        for sec in act["sections"]:
            for path, text in sec["files"].items():
                write(out, path, text)
            git(out, "add", "-A")
            if not git(out, "status", "--porcelain"):
                sys.exit(f"{message(act, sec).splitlines()[0]}: changes nothing")
            when = commit_date(act["enacted"], len(commits) + 1)
            env = {
                **os.environ,
                "GIT_AUTHOR_NAME": act["act"], "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL, "GIT_AUTHOR_DATE": when,
                "GIT_COMMITTER_NAME": COMMITTER[0], "GIT_COMMITTER_EMAIL": COMMITTER[1], "GIT_COMMITTER_DATE": when,
            }
            git(out, "commit", "-q", "--cleanup=whitespace", "-F", "-", env=env, input=message(act, sec))
            commits.append((act["enacted"], git(out, "rev-parse", "HEAD").strip()))

    # Completed years only, so a tag never moves once the year is over.
    for year in range(commits[0][0].year, date.today().year):
        shas = [sha for enacted, sha in commits if enacted <= date(year, 12, 31)]
        git(out, "tag", f"{year}-12-31", shas[-1])
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(build(sys.argv[1], sys.argv[2]))
