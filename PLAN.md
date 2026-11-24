# Implementation plan

Draft of 21 Nov 2026. Week counts assume part-time work and access to the club's DGX A100 machine. Section 5's week numbers are for this project on its own; section 10 shows how they shift when both projects run together.

**Contents**

1. Goal and scope
2. Key decisions
3. System overview
4. Data model
5. Milestones (M0 to M4)
6. Repository layout
7. Compute plan
8. Legal and licensing checks
9. Risks and fallbacks
10. Running both projects

## 1. Goal and scope

**Goal.** An automatically maintained, verifiable version history of Indian central law, plus evidence that a small model with a verifier applies amendments as accurately as a much larger model, at a fraction of the cost.

**In scope**

- The Constitution of India, with every amendment since 1951.
- 20 heavily amended central acts.
- Changes made by amending acts, including the commencement notifications that bring provisions into force.
- English text.

**Out of scope for v1**

- State acts (a stretch goal after M4).
- Ordinances and other instruments that change law outside amending acts. Track them as notes, not commits.
- The Hindi text of acts.
- Subordinate legislation (rules and regulations), except as input to the linter.
- Legal advice, summaries and question answering.

## 2. Key decisions

| Decision | Why |
|---|---|
| The model proposes edits; an engine applies them; a verifier judges them | A mistake becomes a failed check or a reviewer flag, never a silent change to legal text |
| A small edit language (about ten operations) with grammar-constrained decoding | Every output parses, so the remaining errors are about meaning, not syntax |
| Edit targets must be nodes that actually exist in the act | Removes hallucinated targets entirely |
| Rule-based baseline before any model | Many amendments are formulaic. The model has to earn its place on the rest |
| Train on UK data, Indian silver data and synthetic amendments | legislation.gov.uk has exact before and after versions under an open licence; Indian gold data is scarce |
| The "giant" baseline is an open ~70B model on the DGX; frontier models only on a small sample | The budget is free tiers only |
| Git history in enactment order, with legal dates stored per change | Retrospective amendments break a single timeline (see "Two timelines" in section 4) |
| One file per section | Keeps blame readable and diffs local |
| Unofficial, always linking the official text | Liability and trust |

Record new decisions in `notes/decisions.md`, using the same notes convention as `capstone_project`.

## 3. System overview

```mermaid
flowchart LR
  W["Gazette watcher"] -->|new amending act| SRC["Sources: India Code, Gazette PDFs, legislation.gov.uk"]
  SRC --> P["Parser: act text to tree"]
  P --> M["Sanshodhan-1.5B: amendment text to edit operations"]
  M --> X["Executor: applies edits to the tree"]
  X --> V["Verifier"]
  V -->|pass| PUB["Publish: commit or pull request"]
  V -->|fail| R["Repair: retry with diagnostics, up to 3 times"]
  R --> M
  R -->|still failing| HR["Human review"]
  HR --> PUB
  PUB --> REPO[("Git repositories")]
  REPO --> READER["Reader site"]
```

## 4. Data model

**The act tree.** Act → Part → Chapter → Section → Sub-section → Clause → Sub-clause → Item. Provisos, Explanations, Illustrations and Schedules attach where they appear. Every node has a stable ID written the way lawyers cite it, such as `s.14(1)(c)` or `art.15(4)`, plus a heading, its text and its children.

**Storage in git.** One Markdown file per section (per article for the Constitution), in folders per part and chapter. YAML front matter holds the node ID and its provenance.

**The edit language.** About ten operations. Each one carries its provenance: the amending act, the section, the Gazette reference, the date of enactment, the date it took effect, and whether it is retrospective.

| Operation | Drafting it covers |
|---|---|
| `SUBSTITUTE_WORDS target "old" -> "new"` | "for the words 'thirty days', the words 'fifteen days' shall be substituted" |
| `INSERT_WORDS target after "anchor" "text"` | "after the word 'State', the words 'or Union territory' shall be inserted" |
| `OMIT_WORDS target "text"` | "the words 'or any of them' shall be omitted" |
| `SUBSTITUTE_NODE target block` | "for clause (b), the following clause shall be substituted, namely:—" |
| `INSERT_NODE after/before target block` | "after clause (3), the following clause shall be inserted, namely:—" |
| `ADD_AT_END target block` | "at the end, the following proviso shall be added, namely:—" |
| `OMIT_NODE target` | "clause (c) shall be omitted" |
| `RENUMBER target -> new_id` | "sub-section (2) shall be renumbered as sub-section (2A)" |
| `SCHEDULE_ROW insert/omit/substitute` | Amendments to tables in Schedules |
| `COMMENCE target date` | Commencement notifications |

The quoted drafting shows the style; it isn't quoted from a specific act.

**Two timelines.** Every change has a *valid* date (from when it applies in law) and a *record* date (when it was enacted or notified). A 2019 amendment can apply from 2015. Git commits follow record order. The reader computes "as in force on date D" from the valid dates, and can also show "as published on date D". This is a bitemporal data problem.

**Pre-1970 dates.** Git can't store commit dates before 1970. Put the legal dates in commit trailers (`Enacted:`, `In-Force:`, `Amending-Act:`, `Gazette:`), give older commits an order-preserving placeholder timestamp, and have the reader display the trailer dates.

## 5. Milestones

| Milestone | Weeks | Ends with |
|---|---|---|
| M0 · Hand-built proof | 1–2 | Article 15, the Preamble and one small act on GitHub with blame |
| M1 · The engine | 3–6 | Parser, executor and regex baseline reproducing official consolidated texts |
| M2 · Sanshodhan v0 | 6–12 | The model, the evaluation harness, and the comparison against a 70B model |
| M3 · Coverage | 12–18 | The Constitution and 20 acts versioned; the reader and the linter public |
| M4 · Live | 18 onward | The gazette watcher, the benchmark release, the paper and the video |

### M0 · Hand-built proof (weeks 1–2)

**Goal:** the "Constitution on GitHub, with blame" moment, built by hand before any ML.

1. **Write `history.yaml`** for Article 15, the Preamble and one small act. The Right to Information Act, 2005 is a good candidate: it's short and well known, and it has recent amendments (the 2019 amendment, and the 2023 change to section 8(1)(j) made by the Digital Personal Data Protection Act). Confirm the full amendment list on India Code.
2. **Write `build_repo.py`,** which turns the YAML into files and commits with trailers.
3. **Build reader v0:** a static page that reads git history (exported to JSON by a script) and renders blame, a diff between two dates, and a date slider. The concept mockup's blame and time-travel screens are the starting point.
4. **Publish** to a public GitHub repository and post the blame screenshot.

**Gate.** It's live and correct: every clause's blame matches India Code's footnotes. The reaction tells you how far to take coverage.

**Output:** the public repository and reader v0.

### M1 · The engine (weeks 3–6)

**Goal:** parse acts, apply edits deterministically, and reproduce known consolidated texts with a rule-based baseline.

1. **Ingest.**
   - India Code: principal acts with their footnotes, and amending acts. Cache everything and rate-limit requests.
   - Gazette PDFs where India Code lacks an amending act. Use OCR (Surya or Tesseract) for scans, and check OCR output against a digital copy wherever one exists.
   - legislation.gov.uk: XML for UK acts with their dated versions, plus the "changes" records (which provision changed which, and how).
2. **Write the parser.**
   - Rule-based, covering numbering patterns ("1.", "(1)", "(a)", "(i)"), "Provided that", "Explanation.—" and Schedules.
   - A small classifier as a fallback for ambiguous lines.
   - Round-trip tests on at least 30 acts: parse, render, compare.
3. **Implement the edit language and the executor,** with property tests and error messages precise enough to send back to the model as repair diagnostics.
4. **Align India Code's footnotes.** Parse footnotes of the form "Subs. by Act <n> of <year>, s. <k> (w.e.f. <date>)" into (target node, amending act, section, date). These are weak labels saying which amendment touched which provision.
5. **Write the regex baseline** for formulaic patterns: "for the words X, the words Y shall be substituted", "after clause (b), the following clause shall be inserted", "clause (c) shall be omitted", "shall be renumbered as". Measure how many amendment sentences it matches and how accurate it is.
6. **Run a reconstruction test.** Start from the enacted text of three acts, apply every amendment with the baseline, and compare against India Code's current text.

**Gate.** The engine and baseline reproduce at least two acts' current text exactly, or every difference is explained.

**Output:** the engine, and the baseline's coverage and accuracy numbers.

### M2 · Sanshodhan v0 (weeks 6–12)

**Goal:** a small model that clearly beats the baseline on non-formulaic amendments and matches a 70B open model.

1. **Build datasets.**
   - **UK:** derive (amending text plus target context) → edit operations by diffing dated versions and aligning them with the changes records. Keep only change types the edit language covers.
   - **Indian silver:** amendments where the baseline's edits reproduce India Code's text exactly.
   - **Indian hard set:** amendments the baseline can't handle. Hand-label 200–400 with law students; 200 of them become the frozen IndiaAmend-200 test set.
   - **Synthetic:** random valid edits on real act trees, rendered into Indian drafting language with templates and paraphrased by the 70B model. Keep only the items the executor confirms.
   - **Splits:** by amending act, never by sentence, so nothing leaks between train and test. Freeze IndiaAmend-200 at the start of M2.
2. **Train the model.** A 1.5–2B open model (a current small Qwen model, for example). The input is the amendment text plus the target provisions rendered with their IDs; the output is edit operations. Fine-tune on the DGX in bf16, with LoRA or a full fine-tune.
3. **Constrain decoding.** A grammar for the edit language, plus a per-example rule that targets must be IDs present in the input. Use vLLM structured outputs, xgrammar or outlines.
4. **Run the baselines:**
   - the regex baseline;
   - an open ~70B model (for example Llama 3.3 70B or a 72B Qwen model), prompted with the edit-language spec and examples, under the same constraints;
   - a frontier model on at most 100 items within free credits, both rewriting the provision text and writing edit operations.
5. **Build the evaluation harness.** The metrics are defined in [EXPECTED_RESULTS.md](EXPECTED_RESULTS.md).
6. **Add reinforcement learning.** GRPO (TRL's `GRPOTrainer`) with a reward for edits that execute, pass the verifier and match gold, plus a KL penalty against the fine-tuned model. Compare it with fine-tuning alone.

**Gate.** On IndiaAmend-200:

- At least 15 points above the baseline on non-formulaic amendments.
- Equal to the 70B model, or within 2 points of it, at 5% of its cost or less.

**Output:** Sanshodhan v0 on Hugging Face, the evaluation harness, and a draft benchmark.

### M3 · Coverage (weeks 12–18)

**Goal:** the Constitution and 20 acts fully versioned and public, plus the linter.

1. **Choose the 20 acts.** Look for acts that are often cited and often amended, ideally with born-digital amending acts. Starting candidates, to check on India Code:
   - the Code of Civil Procedure, 1908
   - the Indian Contract Act, 1872
   - the Transfer of Property Act, 1882
   - the Negotiable Instruments Act, 1881
   - the Specific Relief Act, 1963
   - the Limitation Act, 1963
   - the Hindu Marriage Act, 1955
   - the Representation of the People Act, 1951
   - the Motor Vehicles Act, 1988
   - the Prevention of Corruption Act, 1988
   - the Arbitration and Conciliation Act, 1996
   - the Foreign Exchange Management Act, 1999
   - the Information Technology Act, 2000
   - the Prevention of Money-Laundering Act, 2002
   - the Right to Information Act, 2005
   - the Protection of Children from Sexual Offences Act, 2012
   - the Companies Act, 2013
   - the Insolvency and Bankruptcy Code, 2016
   - the Central Goods and Services Tax Act, 2017
   - the Consumer Protection Act, 2019
2. **Run the pipeline** on everything. Send flagged edits to a review queue (GitHub pull-request review is enough). Have two reviewers check 10% of items, so you can measure agreement.
3. **Handle commencement.** Parse commencement notifications for in-scope acts and set the valid date per provision. Where a date isn't known, mark it "not yet notified or unknown", and never guess.
4. **Handle retrospective amendments.** Mark them, and test the reader's "as in force on" view against known cases.
5. **Build the full reader.**
   - Table of contents, reading as on any date, blame, diff between any two dates, an amendment timeline and search.
   - Permanent links with a "cite this version" option, and links to the official PDFs.
   - Works on mobile, with a disclaimer on every page.
6. **Build the linter.**
   - References to repealed IPC, CrPC and Evidence Act sections in central acts and in the rules on India Code, each paired with the matching BNS, BNSS or BSA section from the official correspondence tables.
   - Cross-references left dangling by an amendment.
   - Numbering gaps.

   Hand-check 200 flags to measure precision.
7. **Launch publicly** with blog post 1.

**Gate:**

- The Constitution and all 20 acts are versioned.
- At least 98% of provisions are applied automatically, and a person has reviewed the rest.
- The reader is live.

### M4 · Live (week 18 onward)

1. **Run the gazette watcher** on a daily GitHub Actions schedule.
   - Sources, in order of preference: India Code's recent updates, PRS Legislative Research's record of passed bills, and the e-Gazette listings.
   - For each new act, download the PDF, run the pipeline and open a pull request with the verification report. A reviewer merges it and the reader redeploys.
   - Inference runs on the free CI runner, using a 4-bit build of the 1.5B model through llama.cpp.
   - Respect each site's terms. If a source blocks automation (with a CAPTCHA, for example), the watcher alerts you and you drop the PDF in by hand. Never work around a CAPTCHA.
2. **Run error analysis,** then a second reinforcement-learning round.
3. **Release IndiaAmend-200** with a datasheet and an evaluation script.
4. **Write the paper.** Your mentor picks the venue; the NLLP workshop, JURIX and ICAIL are the natural ones. Then blog post 2 and the two-minute video.
5. **Outreach** to legal-tech groups (OpenNyAI, for example), law schools and PRS.

**Done when** every item in [DELIVERABLES.md](DELIVERABLES.md) meets its acceptance criteria.

## 6. Repository layout

One repository for the code, plus one repository per law, kept under a GitHub organisation. These planning docs can stay at the root of the code repository.

The folders below were the first plan. `parse/`, `dsl/` and `baseline/` became one `engine/` folder (`notes/decisions.md`, 22 Nov); the rest are made when their milestone starts.

```
git-blame-the-constitution/
  ingest/    fetch, OCR and clean text from India Code, Gazette PDFs and legislation.gov.uk
  parse/     act text to tree, with round-trip tests
  dsl/       edit-language grammar, executor and tests
  baseline/  regex rules for formulaic amendments
  model/     dataset building, fine-tuning, GRPO, constrained decoding
  verify/    invariants, exact match, round-trip checks
  publish/   tree to Markdown files to git commits
  reader/    static site
  watcher/   scheduled job and pull-request bot
  lint/      repealed-reference and cross-reference checks
  eval/      IndiaAmend-200, the UK held-out set, metrics, baselines
  notes/     papers.md, results.md, observations.md, decisions.md
```

## 7. Compute plan

These are rough estimates. Measure them and update.

| Job | Estimate |
|---|---|
| Ingest and OCR | Hours of CPU time; GPU OCR is optional |
| Fine-tuning the 1.5B model on 50,000–200,000 examples | Hours to a day on 1–8 A100s |
| GRPO | A day or two on 8 A100s |
| The 70B baseline on the test sets | Hours on 4–8 A100s with vLLM tensor parallelism |
| Frontier sample | At most 100 items, within free credits |
| Gazette watcher | Free GitHub Actions minutes; a few amendments a month on CPU |

## 8. Legal and licensing checks

- **Reusing Indian acts.** Indian copyright law has a specific exception for reproducing Acts of a legislature (section 52(1)(q) of the Copyright Act, 1957), and it comes with conditions. Confirm how it applies with a law-faculty member before the public launch.
- **Automated access.** Read the terms of use for India Code and the e-Gazette.
- **UK data.** legislation.gov.uk content is under the Open Government Licence v3.0. Attribute it.
- **Disclaimer.** Every page and repository says it is unofficial, links the official text, and says it isn't legal advice.

## 9. Risks and fallbacks

| Risk | Early sign | Fallback |
|---|---|---|
| PDF or OCR quality | OCR disagrees with digital copies on spot checks | Start with born-digital acts (roughly post-2000) and add older ones later |
| The parser fails on Schedules and tables | Round-trip failures inside Schedules | Treat Schedules as opaque blocks first; add table operations later |
| Indian gold data is too scarce | Hand-labelling falls behind | Lean on UK, silver and synthetic data; cut the hard set to 100 items |
| 1.5B can't match 70B | The M2 gate misses | Try 3B and 7B models, or distil from verified 70B outputs. The claim becomes an accuracy-against-cost curve |
| Commencement dates are unclear | Provisions with unknown in-force dates | Mark them as unknown and never guess |
| Retrospective amendments | Wrong text in "as in force on" views | Two-timeline metadata, and tests on known retrospective cases |
| Automation is blocked | A CAPTCHA, or terms that forbid it | Manual drop-in with alerts |
| Liability | Someone relies on the text as official | Disclaimers, official links and the review queue |

## 10. Running both projects

This project is mostly CPU work and careful engineering, plus one modest fine-tune. lost-in-transcription spends most of its time waiting on GPU jobs that run for days. Build this engine while the speech models train.

| Weeks | Lost in Transcription | git blame the Constitution |
|---|---|---|
| 1–2 | Request data access and DGX time; start the normaliser | M0: the hand-built proof goes public |
| 3–8 | M0 to M1: the atlas goes public | M1: the engine, in the gaps between jobs |
| 8–20 | M2 to M3: Kaan training and the data engine | M2: the Sanshodhan fine-tune shares the GPU queue |
| 20 onward | M4: bot, leaderboard, paper | M3 to M4: coverage, the watcher, paper |

Finishing both properly takes roughly 9–12 months part-time. If time gets tight, lost-in-transcription stays the flagship and this project stops after M2: the result against the 70B model already stands on its own.
