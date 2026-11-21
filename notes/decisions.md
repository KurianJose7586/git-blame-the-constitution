# Decisions

Why things are the way they are, including the ones that were reversed. PLAN.md section 2 holds the decisions made before any code; this file holds everything after.

---

## 2026-11-21: Kickoff defaults (accepted as written in KICKOFF.md)

1. **One commit per section of an amending act, not one per act.** Sections of one act often come into force on different dates, and `In-Force` is a per-commit trailer. Blame then reads "First Amendment, s. 2".
2. **No front matter in the law files** (changes PLAN §4). The path is the ID, the trailers hold the provenance, and GitHub would render front matter as a table above the law.
3. **`Retrospective` is derived:** `yes` exactly when `In-Force` is earlier than `Enacted`.
4. **Permanent links name a date, not a commit.** Correcting an old amendment rebuilds every later commit with new hashes.
5. **Law repositories are build outputs.** History files in the code repository are the source of truth. Builds are deterministic, so appending an amendment is a fast-forward; only corrections to old entries need a force push.
6. **The commit author is the amending act; the committer is KurianJose7586.** Plain `git blame` names the law.
7. **Commencement finer than a file takes the later date,** so the reader never shows text as in force before it was. Each case goes in observations.md.
8. **UK ingest moves from M1 to the start of M2** (changes PLAN M1.1). Nothing reads UK data before then.
9. **Edit operations as JSON** (recommended, changes PLAN §4). One JSON Schema serves the parser and constrained decoding; the DSL stays as the display format. To be confirmed at the start of M1.

## 2026-11-21: Made while building T1–T4

- **Year tags only for completed years** (KICKOFF said up to 2026). A tag for the current year would move whenever a new amendment lands before 31 December.
- **The official-text check compares words, not layout.** It drops our Markdown markup and treats dashes as spaces, so the fixture can be the official text as extracted, line wraps and run-in headings included, rather than a copy retyped into our format. Retyping would make the check compare our typing with itself.
- **The test for "as in force on" dates moves from T4 to T5,** where the date-selection code lives. T4 checks the year tags instead.
- **`.gitattributes` forces LF** in the code repository, because this machine has `core.autocrlf=true`.

## 2026-11-21: Reader v0 (T5, T6)

- **Route format.** `#/<law>/<file>@<date>` reads as in force on a date, `@<from>..<to>` diffs (git's range syntax), `?view=blame` blames, and `?published` switches to the enactment timeline. Every view is a permanent link because all state is in the hash.
- **Blame shows the current text only.** Blame as of an earlier date is cheap (`git blame <sha>`), but nothing needs it before the M3 reader.
- **The date picks a whole-file snapshot, not a replay.** `export.py` refuses a law where a file's in-force dates run out of commit order, so the shortcut can't silently show text early. M1's edit operations lift the limit.
- **`export.py` also writes `laws.json`,** the list of laws for the home page, from whatever law JSON sits beside it.
- **No framework or build step.** Plain ES module, one HTML file with inline CSS, jsdiff 5.2.0 from jsDelivr for word diffs. `reader/package.json` only tells Node that `app.js` is a module, for the tests. The jsdiff tag has no integrity hash yet: add one before the public launch.
- **The slider re-renders on release (`change`), not while dragging,** because re-rendering replaces the slider mid-drag.
