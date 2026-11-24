# git blame the Constitution

Every Indian law as a git repository, rebuilt automatically from the text of its amendments.

Parliament changes laws with patches written in English: "for the words 'thirty days', the words 'fifteen days' shall be substituted". People still apply those patches by hand, and the Legislative Department's own dashboard lists central act texts as "under updation". This project trains a small model, **Sanshodhan-1.5B** ("sanshodhan" is Hindi for amendment), that turns amendment text into edit operations. A deterministic engine applies them and a verifier checks the result before anything is committed. The output is a git history of Indian law with blame, diff and time travel, kept current by a bot.

## What exists at the end

| Deliverable | What it is |
|---|---|
| The law, in git | One repository per law, starting with the Constitution and 20 heavily amended central acts, with one commit per amendment |
| The reader | Website: read any act as it stood on any date, blame, diff between dates, permanent links for citing |
| Sanshodhan-1.5B and `amend` | The model on Hugging Face, plus a pip-installable command-line tool (apply, verify, lint) |
| Gazette watcher | A scheduled job that opens a pull request when a new amendment appears |
| Law linter | Reports of references to repealed law (IPC to BNS, CrPC to BNSS, Evidence Act to BSA) and broken cross-references |
| IndiaAmend-200 and write-up | A hand-checked benchmark, a paper, blog posts and a two-minute video |

Acceptance criteria for each one are in [DELIVERABLES.md](DELIVERABLES.md).

## Documents

| File | Contents |
|---|---|
| [PLAN.md](PLAN.md) | Phased implementation plan (M0 to M4), key decisions, data model, architecture, compute, legal checks, risks, and how this runs alongside lost-in-transcription |
| [KICKOFF.md](KICKOFF.md) | How M0 and M1 get built: file formats, commit format, reader data, tasks with done-when, and what needs you |
| [M2.md](M2.md) | How M2 gets built: the task format, the datasets and IndiaAmend-200, the baselines, the model, the gate, and what needs you (a draft) |
| [DELIVERABLES.md](DELIVERABLES.md) | Every deliverable with its definition of done |
| [EXPECTED_RESULTS.md](EXPECTED_RESULTS.md) | Metrics, baselines, experiments, targets, and what you can still claim if a target is missed |

## Status

M0's public part is done (KICKOFF.md tasks T1–T9): the Constitution's Preamble and Article 15, and the whole Right to Information Act, 2005 (14 commits, including seven Second Schedule notifications up to CERT-In in 2023), build into git repositories whose blame matches the official footnotes. They're public, and reader v0 reads, blames and diffs them on any date. Left for the M0 gate: the hand checks in [notes/m0-gate.md](notes/m0-gate.md).

- Reader: https://kurianjose7586.github.io/git-blame-the-constitution/
- [india-law/constitution](https://github.com/india-law/constitution) ([blame on Article 15](https://github.com/india-law/constitution/blame/main/part-iii/article-015.md))
- [india-law/rti-act](https://github.com/india-law/rti-act)

![Blame on Article 15 in the reader: 1950, 1951, 2006 and 2019 in four colours](screenshots/blame-article-15.jpg)

Build each repository and the reader's data, then serve the reader at http://localhost:8123:

```
uv run publish/build_repo.py history/rti-act.yaml out/rti-act
uv run publish/export.py out/rti-act reader/data/rti-act.json
python -m http.server 8123 --directory reader
```

The same two commands work for `constitution`.

M1 is done, its gate met on "every difference explained" ([notes/results.md](notes/results.md)). It built the edit operations and executor (`engine/ops.py`), a regex baseline (`engine/baseline.py`), and a replay of M0's history through both, which reproduces 12 of its 16 amendments exactly and 15 word for word:

```
uv run engine/replay.py history/constitution.yaml history/rti-act.yaml
```

The whole current Constitution (the Preamble, 471 articles and the 12 Schedules) now parses from the Legislative Department's PDF into law files, with each of its 773 footnotes linked to the lines it covers and the amendment that made them. Every file's words match the source, the articles match the Constitution's own list of contents, and the Preamble and Article 15 come out identical to M0's hand-built files. From those footnotes, `engine/rebuild.py` rebuilds a silver history of the whole Constitution, 443 commits back to 1950; `git blame` works on every line, and its 1950 text is checked against M0's Article 15 and Preamble. The same parser, with `--act`, reproduces M0's RTI Act. All of this stays local until the permission requested under T10 arrives:

```
uv run ingest/pdf.py sources/coi-2026-09-10.pdf out/coi.txt
uv run engine/constitution.py out/coi.txt out/constitution-current
uv run engine/rebuild.py out/coi.txt out/constitution-silver.yaml
uv run publish/build_repo.py out/constitution-silver.yaml out/constitution-silver
```

T18 then rebuilt three more Acts from their amendments and checked them against official consolidations: the Insolvency and Bankruptcy Code to 2021, POCSO to 2019 and the Arbitration and Conciliation Act to 2021, every difference explained. M2 ([M2.md](M2.md)) has started: those replays give 75 checked examples of amending text and the edit operations it makes. From the downloads in `sources/` (hashes in `notes/sources.sha256`):

```
uv run model/build-replays.py
sh model/build-silver.sh
```

An audit on 24 Nov ([notes/audit-2026-11-24.md](notes/audit-2026-11-24.md)) found errors that gave wrong text without an error in the parser, the rebuild, the executor and the reader; they're fixed and tested, and `notes/results.md` restates the numbers they changed.

Tests: `uv run pytest` and `node --test reader/app.test.mjs`.

## First week

1. Write the amendment history of Article 15 and the Preamble by hand as a YAML list, using India Code and the amending acts as sources.
2. Write the script that turns that YAML into a git repository, and a minimal page that renders blame and diff.
3. Pick the small act for M0 and draft the list of 20 acts. [PLAN.md](PLAN.md) has candidates for both, under M0 and M3.
4. Ask your mentor for a law-faculty contact. You'll need law students for review, and someone to confirm the reuse terms for Indian legal texts before the public launch.

## Links

- Concept mockup (private to you): https://claude.ai/artifact/TjPSty3edyvHhbFByaM7LT
- Sibling project: [../lost-in-transcription](../lost-in-transcription)
- India Code: https://www.indiacode.gov.in
- legislation.gov.uk (training data under the Open Government Licence): https://www.legislation.gov.uk
- Closest prior work, algorithmic legislative consolidation: https://arxiv.org/abs/2501.16794
