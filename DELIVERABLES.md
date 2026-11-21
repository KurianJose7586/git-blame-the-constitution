# Deliverables

Each deliverable has a definition of done. A deliverable isn't finished until every box under it is ticked. Milestones refer to [PLAN.md](PLAN.md).

## 1. The law, in git

**Milestone:** M0 proof, M3 coverage. **Lives on:** a GitHub organisation, one repository per law.

- [ ] The Constitution (every amendment since 1951) and 20 central acts.
- [ ] One Markdown file per section (per article for the Constitution).
- [ ] One commit per amendment, with trailers: `Amending-Act`, `Section`, `Gazette`, `Enacted`, `In-Force`, `Retrospective`.
- [ ] Tags for each year, so anyone can check out the law as it stood on 31 December of that year.
- [ ] A README per repository with the disclaimer and links to the official text.
- [ ] CI that fails any commit the verifier rejects.

## 2. The reader

**Milestone:** M0 prototype, M3 full. **Lives on:** GitHub Pages or Vercel (free tier).

- [ ] Read any act as in force on any date, plus "as published on" a date where retrospective amendments make the two differ.
- [ ] A blame view with era colours; hovering a block shows its amendment and source.
- [ ] A diff between any two dates.
- [ ] An amendment timeline and search.
- [ ] Permanent links to each version of each provision, with a "cite this version" option.
- [ ] Works on mobile, with a disclaimer on every page.

## 3. Sanshodhan-1.5B

**Milestone:** v0 at M2, v1 at M4. **Lives on:** Hugging Face.

- [ ] Weights, plus a 4-bit build that runs on a CPU.
- [ ] A model card with IndiaAmend-200 and UK results next to the regex baseline, the 70B model and the frontier sample, plus training data, licence, limitations and intended use.
- [ ] A training recipe that reproduces the release.

## 4. The `amend` command-line tool

**Milestone:** M2 to M3.

- [ ] Installs with pip and runs on a CPU.
- [ ] `amend apply <act> <amending act PDF or text>` writes the edit operations, the patched files and a verification report.
- [ ] `amend verify` checks an existing repository.
- [ ] `amend lint` runs the linter.

## 5. Gazette watcher

**Milestone:** M4.

- [ ] Runs on a daily schedule within free GitHub Actions minutes.
- [ ] Opens a pull request with the edit operations, the diff and the verification report for every new amending act it detects.
- [ ] Median time from detection to pull request of 15 minutes or less.
- [ ] Sends an alert when a source can't be fetched, and supports dropping a PDF in by hand.
- [ ] Follows each site's terms and never works around a CAPTCHA.

## 6. Law linter reports

**Milestone:** M3.

- [ ] A public report of references to repealed IPC, CrPC and Evidence Act sections, each with the matching BNS, BNSS or BSA section.
- [ ] Lists of dangling cross-references and numbering gaps.
- [ ] Precision of at least 90% on a hand-checked sample of 200 flags.

## 7. IndiaAmend-200

**Milestone:** frozen at the start of M2, released at M4.

- [ ] 200 hand-checked Indian amendments, each with gold edit operations and the gold resulting text, split by amending act.
- [ ] A datasheet covering sources, labelling procedure, reviewer agreement and licence.
- [ ] An evaluation script that reproduces the paper's numbers.

## 8. Write-ups

**Milestones:** blog post 1 at the M3 launch (a short post at M0 is optional); the paper, blog post 2 and the video at M4.

- [ ] Blog post 1: "The Constitution is on GitHub, with blame".
- [ ] Paper: the system, IndiaAmend-200, the small-against-large comparison, ablations and error analysis.
- [ ] Blog post 2: how the model and verifier work, and what the linter found.
- [ ] A two-minute demo video following this script:

| Time | Shot |
|---|---|
| 0:00 | `git log --oneline` on the Constitution scrolls through seven decades of amendments |
| 0:15 | Blame on Article 15: four eras in four colours, 1950 to 2019 |
| 0:35 | The Preamble from 1976 to 1977: "SOCIALIST SECULAR" and "integrity" appear as a diff |
| 0:55 | Paste an amending act; the model writes edit operations and the verifier flags a dangling reference |
| 1:20 | The comparison: exact match against the 70B model, and what each one costs |
| 1:40 | The gazette watcher's latest pull request |
| 1:50 | The linter's list of rules still citing IPC sections, with their BNS equivalents |

## 9. Notes

**Ongoing.** `notes/papers.md`, `notes/results.md`, `notes/observations.md` and `notes/decisions.md`, kept the same way as in `capstone_project`.

## Portfolio package

When everything above is done, the code repository's README should link the law repositories, the reader, the model, the benchmark, the paper, the video and both blog posts, and state the result in one line. The template for that line is in [EXPECTED_RESULTS.md](EXPECTED_RESULTS.md#the-headline).
