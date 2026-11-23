# Kickoff: how M0 and M1 get built

Written 21 Nov 2026 from PLAN.md, DELIVERABLES.md and the concept mockup. PLAN.md says what to build and in what order. This file says how: the file formats, the scripts, and when each task counts as done. It covers M0 and M1 only, because M2 onward depends on numbers that M1 produces; [M2.md](M2.md) picks up from there. Revisit at the M0 gate.

Tools on this machine are enough for M0: Python 3.12, uv 0.7, git 2.50 and Node 22. The only new Python dependency is `pyyaml`.

## Decisions this plan makes

Each one is a default. Object before T1 starts. Otherwise they go into `notes/decisions.md` as written. The ones marked **(changes PLAN)** depart from PLAN.md.

1. **One commit per section of an amending act, not one per act.** Sections of one act often come into force on different dates (sections of the 42nd Amendment started on several dates in 1977, and s. 2, which changed the Preamble, started on 3 January), and `In-Force` is a per-commit trailer. This also makes blame read "First Amendment, s. 2", as it does in the mockup.
2. **No front matter in the law files (changes PLAN §4).** The path is already the ID (`part-iii/article-015.md` is art. 15) and the trailers already hold the provenance. GitHub would also render front matter as a table above the law. Add front matter back if the parser needs something the path can't hold.
3. **`Retrospective` is derived, not typed.** It is `yes` exactly when `In-Force` is earlier than `Enacted`.
4. **Permanent links name a date, not a commit.** Fixing a typo in an old amendment rebuilds every later commit with new hashes. A link like `#/constitution/part-iii/article-015@2006-01-20` still works after that, and a link to a SHA doesn't.
5. **Law repositories are build outputs.** The history files in the code repository are the source of truth. Builds are deterministic, so adding an amendment at the end only appends a commit and the push is a fast-forward. Only corrections to old entries need a force push. In M4 the watcher's pull request goes against the history file, and CI rebuilds the law repository.
6. **The commit's author is the amending act and the committer is you.** Plain `git blame` and `git log` in a terminal then name the law, which is what the demo video opens on. The alternative is you as author too, with the act only in the trailers.
7. **Commencement finer than a file takes the later date.** RTI ss. 4(1), 5(1) and 5(2) came into force on 15 June 2005, and the rest of ss. 4 and 5 on 12 October 2005. Until M3's commencement work, the whole file takes the later date, so the reader never shows text as in force before it was. Each such case gets a line in `notes/observations.md`.
8. **The UK ingest moves from M1 to the start of M2 (changes PLAN M1.1).** Nothing reads UK data before the M2 datasets.
9. **Edit operations as JSON (recommended for M1, changes PLAN §4).** One JSON Schema gives you the Python parser (stdlib `json`) and constrained decoding (vLLM's structured outputs take a schema directly). The target-ID rule becomes a per-example `enum`, and quoting law text needs no escape rules of your own. The DSL in PLAN §4 stays as the display format in pull requests. Decide at the start of M1. Nothing in M0 depends on it.

## Repositories

| Repository | Holds |
|---|---|
| `git-blame-the-constitution` (this folder, your account) | Code, history files, reader, these docs and `notes/` |
| `<org>/constitution` | Built from `history/constitution.yaml` |
| `<org>/rti-act` | Built from `history/rti-act.yaml` |

- Pick the organisation name. The mockup uses `india-law`, so check whether it's free. You create the organisation and the two empty law repositories.
- The reader deploys to GitHub Pages from `reader/` using the standard Pages workflow (`upload-pages-artifact`, then `deploy-pages`). The workflow runs the build and the export, so generated JSON is never committed.
- The code repository's first commit holds these docs, a `.gitignore` (`out/`, `.venv/`, `__pycache__/`, `reader/data/`, `cache/`) and `pyproject.toml`.

M0 layout, a subset of PLAN §6:

```
history/   constitution.yaml, rti-act.yaml
publish/   build_repo.py, export.py
reader/    index.html, app.js, app.test.mjs
tests/     test_publish.py, official/ (the current official text, as extracted)
notes/     papers.md, results.md, observations.md, decisions.md
```

## Contracts

The pieces only agree on these four formats. Everything else can change freely. In M1 the engine writes the same history format, so `build_repo.py` doesn't change when hand entry stops.

### 1. History file: `history/<law>.yaml`

One entry per amending act, in order of enactment, each with one or more sections. Each section gives the full text of every file it changes, as the file reads afterwards. `null` deletes a file.

```yaml
law: constitution
title: The Constitution of India
official: https://www.indiacode.nic.in/...    # the official text, linked from the README and the reader
amendments:
  - act: The Constitution of India
    enacted: 1949-11-26
    source: https://...
    sections:
      - section: null
        in_force: 1950-01-26
        files:
          preamble.md: |
            ...
          part-iii/article-015.md: |
            ...
  - act: The Constitution (First Amendment) Act, 1951
    enacted: 1951-06-18
    gazette: ...                               # optional
    source: https://...                        # PDF of the amending act
    sections:
      - section: "2"
        in_force: 1951-06-18                   # null means not notified or unknown. Never guess
        text: |                                # the amending provision, verbatim
          In article 15 of the Constitution, the following clause shall be added, namely:—
          ...
        files:
          part-iii/article-015.md: |
            (the whole article after the change)
```

The file holds hand-entered snapshots, not edit operations. M0 is the proof built by hand, and every snapshot is gold text that M1's engine has to reproduce. The verbatim `text` is the input that M1's baseline and M2's model will read.

### 2. Law files

- One file per article or section: `preamble.md`, `part-iii/article-015.md`, `chapter-ii/section-008.md`, `schedule-2.md`. Numbers are padded to three digits so GitHub lists them in order. Inserted provisions keep their letter (`article-021a.md`).
- The first line is the heading, and after it comes one line per provision, so blame resolves to the clause. Depth is a nested Markdown list, two spaces per level:

  ```markdown
  # 15. Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth.

  - (1) The State shall not discriminate against any citizen on grounds only of religion, race, caste, sex, place of birth or any of them.
  - (2) No citizen shall, on grounds only of religion, race, caste, sex, place of birth or any of them, be subject to any disability, liability, restriction or condition with regard to—
    - (a) access to shops, public restaurants, hotels and places of public entertainment; or
    - (b) the use of wells, tanks, bathing ghats, roads and places of public resort maintained wholly or partly out of State funds or dedicated to the use of the general public.
  - (3) Nothing in this article shall prevent the State from making any special provision for women and children.
  ```

  Depth can't be inferred from labels. In RTI s. 2, clause (i) defines "record" and has its own (a) to (d), so "(i)" there is a clause, not a sub-clause. Writing the depth down also hands M1's parser its tree for free.
- Text is verbatim from the official source, with the same quotes, dashes and "per cent.". Provisos and Explanations get their own lines (`- *Provided that* …`, `- *Explanation*.—…`). India Code's footnote markers (`1[…]`) are stripped, because that information becomes commits. Where the source sets text on separate lines, as the Preamble does (JUSTICE, LIBERTY, …), keep those lines.

### 3. Commits

```
The Constitution (First Amendment) Act, 1951, s. 2

In article 15 of the Constitution, the following clause shall be added, namely:—
…

Amending-Act: The Constitution (First Amendment) Act, 1951
Section: 2
Gazette: …
Enacted: 1951-06-18
In-Force: 1951-06-18
Retrospective: no
Source: https://…
```

- **Identity:** the author is the amending act with an `@invalid` address, and the committer is you (decision 6). Both are fixed in the script.
- **Dates:** the enactment date at 12:00 IST. Git can't store dates before 1970, so those commits get `1970-01-01T00:00:00Z` plus one second per commit, which keeps the order. The trailers hold the real dates.
- **Tags:** one per completed year, from the year of the first commit (`1949-12-31`, `1950-12-31`, …). Each points at the last commit enacted on or before that day, so `git checkout 1977-12-31` gives the law as published at the end of 1977. Dated names rather than bare years, so a tag can't be read as a short hash. Git has one timeline, so the "as in force" view lives in the reader.
- **README:** the first commit adds it, with the title, a link to the official text, and the "unofficial, not legal advice" disclaimer.
- **Determinism:** the same history file always gives the same hashes. Write files with LF line endings and set `core.autocrlf=false` in the generated repository. This machine has `autocrlf=true`, which would otherwise make a Windows build and the Linux CI build disagree.

### 4. Reader data: `reader/data/<law>.json`

`export.py` reads a law repository, not the history file, so the same export works on the commits M4's bot makes.

```json
{
  "version": 1,
  "law": "constitution",
  "title": "The Constitution of India",
  "official": "https://www.indiacode.nic.in/...",
  "commits": [
    {"sha": "…", "act": "The Constitution (First Amendment) Act, 1951", "section": "2",
     "gazette": "…", "enacted": "1951-06-18", "in_force": "1951-06-18",
     "retrospective": false, "source": "https://…", "text": "…"}
  ],
  "files": [
    {"path": "part-iii/article-015.md",
     "versions": [{"commit": 0, "text": "…"}, {"commit": 1, "text": "…"}],
     "blame": [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 3, 3]}
  ]
}
```

- `versions` holds the file's text after each commit that touched it, as an index into `commits`. `text` is `null` after a deletion.
- `blame` gives, for each line of the current text, the commit that last changed it, taken from `git blame --porcelain`.
- **As in force on date D** is the latest version whose commit has `in_force` on or before D. **As published on D** is the same rule using `enacted`. That shortcut is only right while each file's in-force dates run in the same order as its commits, so `export.py` fails loudly when they don't. The general case needs a replay of edit operations, which M1 provides. None of M0's data hits it.

## M0 tasks (weeks 1–2)

| # | Task | Done when |
|---|---|---|
| T1 | Code repository: `git init`, a `uv` project (`pyyaml`, with `pytest` as a dev dependency), `.gitignore`, `notes/` with its four files, and the decisions above copied into `decisions.md` | `uv run pytest` runs |
| T2 | `history/constitution.yaml`: the Preamble and Article 15 in five commits. These are the text as adopted; the First Amendment, s. 2 (18 Jun 1951); the 42nd, s. 2 (enacted 18 Dec 1976, in force 3 Jan 1977); the 93rd, s. 2 (20 Jan 2006); and the 103rd, s. 2 (enacted 12 Jan 2019, in force 14 Jan 2019). Paste India Code's current text into `tests/official/`, and write its footnotes down as the table of expected blame | The file loads and every date has a source |
| T3 | `publish/build_repo.py <history> <out>`: refuses an existing `<out>`, writes the files, commits with trailers, sets dates and identities, tags years, adds the README | The constitution build passes T4 |
| T4 | `tests/test_publish.py` builds into a temp folder and checks four things. (a) The current text has the same words as `tests/official/`, ignoring layout and markup. (b) Every line's blame matches the footnote table. (c) Two builds give the same HEAD hash. (d) The year tags fall on the right side of the 42nd Amendment | Passes, and breaking any footnote makes it fail |
| T5 | `publish/export.py <repo> <out.json>`, following contract 4 | The reader loads its output, and date selection gives the right Preamble on 2 Jan 1977 and 3 Jan 1977, and on 20 Dec 1976 as published |
| T6 | Reader v0: `index.html` and `app.js`, with no build step. **Read:** a table of contents, then any file as in force or as published on a date, using a native `<input type="date">` plus a slider over the amendment dates. **Blame:** era colours, and hovering or tapping a block shows its commit card, as in the mockup. **Diff:** word level between two dates, using jsdiff pinned on a CDN. Hash routes are the permanent links. Every view has the disclaimer and the official link. Start from the mockup's styles. `node --test` covers the date-selection function | All three views work on the constitution data at 375 px wide, and `node --test` passes |
| T7 | `history/rti-act.yaml`: the enacted text (Act 22 of 2005) goes in as two commits, one per commencement date in s. 1(3), then each amendment. Take the enacted wording from the Gazette copy; India Code's footnotes give the replaced words. The expected amendments, to confirm on India Code, are: the RTI (Amendment) Act, 2019 (Act 24 of 2019), ss. 2–4, on ss. 13, 16 and 27; the Digital Personal Data Protection Act, 2023, s. 44(3), on s. 8(1)(j), checking its commencement notification; whether the Jammu and Kashmir Reorganisation Act, 2019 touched s. 1(2); and the Second Schedule notifications (see "Needs you") | T4's checks pass for the RTI Act too |
| T8 | Publish: push both law repositories, add the Pages workflow, deploy | The public URLs work and the blame screenshot is taken |
| T9 | Draft the list of 20 acts. For each candidate under PLAN M3, record how many amending acts India Code lists, and whether the amending acts are born-digital PDFs. Pick M1's three reconstruction acts from it | The table is in `notes/decisions.md` |

Order: T1, T2, T3 with T4, T5, T6, T7, T8. Fit T9 into gaps.

### M0 gate

- T4 passes for both laws. Every clause's blame matches India Code's footnotes, which is PLAN's gate written as a test.
- Check the reader's three views by hand against India Code on each commit date.
- Post the blame screenshot (a blog post is optional) and note the reaction in `notes/observations.md`. PLAN uses it to decide how far to take coverage.

## M1 tasks (weeks 3–6)

These are rougher; refine them at the M0 gate. Folder names follow PLAN §6.

| # | Task | Done when |
|---|---|---|
| T10 | Read the terms of use for India Code and the e-Gazette. This blocks T11 | **Done 21 Nov.** India Code bans automated access and reproduction without written permission; its APIs are offered through API Setu. Requests drafted in `notes/permission-requests.md` |
| T11 | `ingest/`: fetch the three acts' texts and amending acts into `cache/`, never refetching. **Revised after T10, and on 22 Nov:** the sources are the e-Gazette and files you download by hand into `sources/`. API Setu is dropped; India Code is read by script only if the Legislative Department gives written permission | Three acts are cached, and a re-run makes no requests |
| T12 | `ingest/pdf.py`: text from born-digital PDFs. Use OCR only for scans, and check it against a digital copy wherever one exists | Text extracted for the amending acts of the three acts. **Started 21 Nov:** the Constitution PDF (402 pages), with lines put back in reading order. **22 Nov:** `--gazette` reads the Gazette's margin notes; the IBC and five of its seven amending Acts extracted (the 2019 Act is a scan, the 2026 Act a Bill layout); POCSO and Arbitration still to come |
| T13 | `parse/`: act text to a tree with IDs written the way lawyers cite them (`s.14(1)(c)`), rendered to contract 2 | Round trip on 30 acts, with experiment E1's numbers in `results.md`. **Constitution done 22 Nov** (`engine/constitution.py`): 471 articles and 12 Schedules, 483/483 on E1's word check, local only. `--act` mode reproduces M0's RTI Act; 28 acts to go |
| T14 | `dsl/`: the edit-operation schema (decision 9) and an executor that applies it to the tree. Error messages must be good enough to send back to a model, such as "`s.13(1)`: 'five years' not found; nearest is 'five year'" | Every operation has tests, and seeded random edits on real trees never crash and never touch nodes outside their target |
| T15 | `ingest/footnotes.py`: turn "Subs. by Act 24 of 2019, s. 2 (w.e.f. 24-10-2019)" into (target, act, section, date, kind) | Parses 95% of the three acts' footnotes, with the rest listed. **Constitution done 22 Nov:** 732 of its 736 change notes, in-sample; RTI 16 of 17; the three acts wait for T18's PDFs |
| T16 | `baseline/`: regex rules for the formulaic patterns in PLAN M1.5 | Coverage and accuracy (experiment E2) in `results.md` |
| T17 | Replay M0's hand-written history through the baseline and the executor | The output reproduces M0's snapshots, or every difference is explained |
| T18 | Reconstruction test on the three acts from T9: enacted text plus every amendment, compared with India Code's current text. The engine writes contract 1, so `build_repo.py` publishes the result unchanged | Two acts match exactly, or every difference is explained (PLAN's gate). **Started 22 Nov on the IBC:** the 2016 Code parses (255 sections, E1 266/266, 99.5% of its words in IBBI's 2018 text); the baseline fully understands 38 of 75 held-out amending provisions. **Replayed 22 Nov, 2016 to 2021** (`engine/reconstruct.py`): 69 of 78 amending provisions apply in full; at IBBI's 2021 text 252 of 319 files match word for word (210 before), and of the 75 files amended 52 match or differ only where the 2016 text already did. **23 Nov: every difference to 2021 explained** (80 of 83 provisions apply; the 2019 Act transcribed from its scan); the 2026 Act, held out, 56 of 71 understood on first reading. **POCSO, 23 Nov:** 2012 text rebuilt from India Code's footnotes; the 2019 Act replayed, 53 of 57 files match, every difference explained. **Arbitration, 23 Nov:** 1996 text rebuilt from a consolidation to 2015; the 2015 Act replayed, 102 of 112 files match; the 2019 Act, held out, 14 of 15 understood. The rebuilt 1996 base agrees with the 1996 Gazette, 94.6% of words in order (its Fifth to Seventh Schedules aside). A consolidation after 2021 would check 2019 and 2021 |

## Needs you

| What | Blocks | When |
|---|---|---|
| Confirm or change the decisions above | T1 | Now |
| **Decided 21 Nov 2026: commit them with an `Instrument: notification` trailer.** The RTI Act's Second Schedule is amended by government notifications under s. 24(2), not by amending acts (the CBI was added this way in 2011). PLAN keeps such instruments out of the commits, but then the repository won't match India Code. Recommended: commit them with an `Instrument: notification` trailer. The alternative is a different small act for M0 | T7 | Before T7 |
| Pick the organisation name, then create it and the two law repositories | T8 | Week 2 |
| Ask your mentor for a law-faculty contact, for reviewers and the section 52(1)(q) question | The public launch at M3, not M0 | Week 1 |
| T18's last Act, and POCSO's last two instruments. From the e-Gazette (Search, then Search by Bill / Assent / Act; the search needs no CAPTCHA, a document opens on your click), into your Downloads: the Arbitration and Conciliation Act, 1996 and its amending Acts of 2015, 2019 and 2021 (Gazette IDs 48447, 167377, 210414, 225832), and the Criminal Law (Amendment) Act, 2018 (188472). The Criminal Law (Amendment) Act, 2013 isn't in the e-Gazette's index, and India Code doesn't list it either (it lists Acts as amended, not amending Acts), so a copy UNHCR keeps on ecoi.net instead; and the Arbitration Act as amended up to 2021 from WIPO Lex, since indiacode.nic.in times out. Both wait for your yes to download | T18 | Now |

## Don't start yet

The model, UK data, the gazette watcher, the linter, the `amend` CLI and the 70B baseline all need the M1 engine. M1's numbers also decide how much of M2 is worth doing.

## First two weeks

- **Day 1:** settle the decisions, do T1, start T2.
- **Week 1:** T2 to T6. The Constitution's five commits work in the local reader.
- **Week 2:** T7 (where most of the typing is), T8 and T9, then the **M0 gate**.
