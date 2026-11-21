# Observations

Things noticed along the way: bugs, contradictions, surprises, dead ends. Append as you go. Do not tidy.

---

## 2026-11-21: Sourcing the Preamble and Article 15 (T2)

- **India Code was down** (HTTP 504 on search and on act pages) all afternoon. Used the Legislative Department's consolidated PDF instead: "The Constitution of India [As on 10th September, 2026]", English version. Its footnotes match India Code's style ("Ins. by … (w.e.f. 20-1-2006)"). Re-check `tests/indiacode/constitution/` against India Code itself once it's back.
- **The consolidated text misquotes the replaced words.** Preamble footnote 2 says the 42nd Amendment substituted for "Unity of the Nation", capital U. Section 2(b) of the Act itself says "unity of the Nation". The 1950 text here follows the Act. Expect more of this: the footnotes' quoted "old text" is weak evidence and needs checking against the amending act. Matters for the T15 footnote parser and for reconstructing enacted texts in M1.
- **The Legislative Department's list of amending acts shows wrong dates.** The 42nd Amendment is listed at 28/08/1976 (assent was 18 Dec 1976), the First at 18/07/1951 (assent 18 June 1951), and many acts at 30/10/2025, which looks like an upload date. Take enactment dates from the act's own text.
- **The 1950 text is reconstructed, not read.** It is the consolidated text with the four amendments reversed, using the amending acts' wording. All four amendments here only insert or substitute, so the reversal is mechanical, but compare with a 1950 printing when one turns up.
- **Scans.** The 103rd Amendment PDF is a pure image scan (no text layer); read from the page images. The 93rd's text layer is poor OCR. The First and 42nd are retyped and clean. Born-digital isn't guaranteed even for recent acts, which PLAN's risk table assumes.
- **Typesetting slips in the Gazette.** The 103rd Amendment runs words together ("institutionsincluding", "existingreservations", "eachcategory"). The commit message uses the spaced form, as the consolidated text does. A model trained on Gazette text will see these.
- **Commencement notification.** The 103rd came into force by S.O. 292(E) of 14 Jan 2019, two days after assent. There's no trailer for the notification yet; it's a comment in the history file.

## 2026-11-21: Build (T3, T4)

- `git blame` on the built `article-015.md` lines up with the four footnotes with no tuning: one line per provision is enough.
- Checked that the tests bite: naming the wrong act in a footnote fails the blame test, a one-word typo in the final text fails the official-text test, and putting clause (4) in the 1950 text stops the build with "The Constitution (First Amendment) Act, 1951, s. 2: changes nothing".

## 2026-11-21: Reader v0 (T5, T6)

- **A two-timeline case already in M0's data:** the 103rd Amendment was enacted on 12 Jan 2019 and came into force on 14 Jan. On 13 Jan 2019 the reader shows Article 15 with clauses (1) to (5) as in force, and with (6) as published. Good for the write-up: the gap needn't be years to matter.
- The Preamble diff from 1950 to today shows exactly the demo-video shot: "SOCIALIST SECULAR" and "and integrity" in green.
- Checked in the browser: all three views, the slider, date box and timeline switch, tapping a blame block, an unknown provision, phone width (375 px, no sideways scroll), and light and dark modes. Not checked: the "copy a link" button, which needs clipboard permission.
- `node --test reader/` fails on Node 22: it wants files or globs, not a folder. Use `node --test reader/app.test.mjs`.
