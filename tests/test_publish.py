"""M0 gate as a test (KICKOFF.md, T4 and T5): built repos match the official text, blame matches its
footnotes, and the export hands the reader the right versions."""
import json
import re
from datetime import date
from pathlib import Path

import pytest
import yaml

from build_repo import build, git
from export import blame, export

ROOT = Path(__file__).resolve().parents[1]
LAWS = sorted(p.stem for p in (ROOT / "history").glob("*.yaml"))


def words(text):
    # Compare words only: drop our Markdown markup, and treat dashes as spaces so a run-in
    # heading ("birth.—(1) The State") matches ours on two lines ("birth." / "- (1) The State").
    # Official consolidated texts mark omissions ("7. ***." for an entry, "India ***." for words) and
    # amendments ("[...]"); our files simply leave omitted text out.
    text = re.sub(r"(\w)-[ \t]*\n\s*", r"\1-", text)  # a word broken after its hyphen: "sub-" / "section"
    text = re.sub(r"^\s*\d+\.\s*\*[\s*]*\.?\s*$", "", text, flags=re.M)
    text = re.sub(r"\s*\*\s*\*\s*\*[\s*]*", "", text)
    text = re.sub(r"^\s*[#-] ", "", text, flags=re.M)
    text = re.sub(r"[*\[\]]", "", text).replace("—", " ")
    return " ".join(text.split())


def law_files(repo):
    return [f for f in git(repo, "ls-files").split("\n") if f.endswith(".md") and f != "README.md"]


def provenance(repo):
    fmt = "%H%x00%(trailers:key=Amending-Act,valueonly)%x00%(trailers:key=Section,valueonly)%x1e"
    out = {}
    for rec in git(repo, "log", f"--format={fmt}").split("\x1e"):
        if rec.strip():
            sha, act, section = (f.strip() for f in rec.split("\x00"))
            out[sha] = (act, section or None)
    return out


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    return {law: build(ROOT / "history" / f"{law}.yaml", tmp_path_factory.mktemp(law) / "repo") for law in LAWS}


@pytest.mark.parametrize("law", LAWS)
def test_matches_official_text(built, law):
    repo, official = built[law], ROOT / "tests" / "official" / law
    expected = {t.relative_to(official).with_suffix(".md").as_posix(): t for t in official.rglob("*.txt")}
    assert sorted(expected) == sorted(law_files(repo)), "every law file needs an official copy, and vice versa"
    for path, txt in expected.items():
        assert words(git(repo, "show", f"HEAD:{path}")) == words(txt.read_text(encoding="utf-8")), path


@pytest.mark.parametrize("law", LAWS)
def test_blame_matches_footnotes(built, law):
    repo = built[law]
    table = yaml.safe_load((ROOT / "tests" / "official" / law / "footnotes.yaml").read_text(encoding="utf-8"))
    acts = provenance(repo)
    used = set()
    for path in law_files(repo):
        for sha, line in blame(repo, path):
            if not line.strip():
                continue
            hits = [i for i, f in enumerate(table["footnotes"]) if f["file"] == path and f["line"] in line]
            assert len(hits) <= 1, f"{path}: several footnotes match {line!r}"
            used.update(hits)
            f = table["footnotes"][hits[0]] if hits else None
            want = (f["act"], f["section"] and str(f["section"])) if f else (table["base"], None)
            assert acts[sha] == want, f"{path}: {line[:60]!r}"
    unused = [table["footnotes"][i]["line"] for i in range(len(table["footnotes"])) if i not in used]
    assert not unused, f"footnotes that match no line: {unused}"


@pytest.mark.parametrize("law", LAWS)
def test_build_is_deterministic(built, law, tmp_path):
    again = build(ROOT / "history" / f"{law}.yaml", tmp_path / "repo")
    assert git(again, "rev-parse", "HEAD") == git(built[law], "rev-parse", "HEAD")


def test_year_tags(built):
    repo = built["constitution"]
    assert "SOCIALIST" not in git(repo, "show", "1975-12-31:preamble.md")
    assert "SOCIALIST" in git(repo, "show", "1976-12-31:preamble.md")  # enacted 18 Dec 1976, in force 1977


def test_export(built, tmp_path):
    data = json.loads(export(built["constitution"], tmp_path / "constitution.json").read_text(encoding="utf-8"))
    files = {f["path"]: f for f in data["files"]}
    commits = data["commits"]
    pre = files["preamble.md"]["versions"]
    assert [(commits[v["commit"]]["enacted"], commits[v["commit"]]["in_force"]) for v in pre] == [
        ("1949-11-26", "1950-01-26"), ("1976-12-18", "1977-01-03")]
    assert "SOCIALIST" in pre[1]["text"] and "SOCIALIST" not in pre[0]["text"]
    # Article 15 at HEAD: seven lines from 1950, then clause (4) from commit 1, (5) from 3, (6) onwards from 4.
    assert files["part-iii/article-015.md"]["blame"] == [0] * 7 + [1, 3] + [4] * 4
    assert commits[1]["text"].startswith("To article 15 of the Constitution")
    assert data["official"].startswith("https://www.legislative.gov.in/")
    assert json.loads((tmp_path / "laws.json").read_text(encoding="utf-8")) == [
        {"law": "constitution", "title": "The Constitution of India"}]


def test_export_refuses_out_of_order_commencement(tmp_path):
    # Enacted 2005 but in force only in 2010, then a 2007 amendment in force at once: the 2007
    # snapshot carries the 2005 change, so "latest version in force" would show it too early.
    history = {"law": "x", "title": "X", "official": "https://example.invalid", "amendments": [
        {"act": f"Act {y}", "enacted": date(y, 1, 1), "source": "https://example.invalid",
         "sections": [{"section": None, "in_force": date(f, 1, 1), "files": {"a.md": f"# A\n\n{y}\n"}}]}
        for y, f in [(2000, 2000), (2005, 2010), (2007, 2007)]]}
    (tmp_path / "x.yaml").write_text(yaml.safe_dump(history), encoding="utf-8")
    repo = build(tmp_path / "x.yaml", tmp_path / "repo")
    with pytest.raises(SystemExit, match="out of commit order"):
        export(repo, tmp_path / "x.json")
