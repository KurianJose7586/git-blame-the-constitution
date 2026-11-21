# Results

Every number produced, and how it was obtained. Append as you go. Never round in the model's favour.

## 2026-11-21: M0's history replayed through the regex baseline and the executor (T16, T17)

**How:** `uv run engine/replay.py history/constitution.yaml history/rti-act.yaml`. For each amending provision in M0's history that has its text (4 Constitution amendments, 5 sections of 3 amending Acts and 7 notifications on the RTI Act), the regex baseline turns the text into edit operations, the executor applies them to the law as it stood before, and the result is compared with the hand-made text after. Three grades: exact; equal after mapping curly quotes to straight and collapsing whitespace; same words (lower-cased letters and digits only).

| | Count |
|---|---|
| Amending provisions | 16 |
| Baseline produced operations for every instruction, none unparsed | 16 |
| Exact match | 12 |
| Match after normalising quotes and whitespace | 13 |
| Same words | 15 |

The four that aren't exact:

- **103rd Amendment, s. 2:** matches after normalising quotes. The amending text in the history file was typed with straight quotes; the article has curly ones.
- **G.S.R. 726(E) of 2008 and 673(E) of 2016:** same words. The notifications put the full stop outside the quote ("26. Strategic Forces Command".), so the entry comes out without one; the history keeps the consolidated form with a full stop (decision of 21 Nov: the primary text wins on words, not punctuation).
- **DPDP Act, 2023, s. 44(3): no match, by one line.** "For clause (j), the following clause shall be substituted", applied literally, replaces clause (j) and leaves the proviso after it. DoPT's consolidation, which the history follows, also drops the proviso. The difference is exactly the contested question of whether that proviso survives.

**Caveats, so nobody rounds this up:** 16 provisions is tiny, and the baseline's rules were written while reading these same 16 texts, so this is in-sample and says nothing yet about how far formulaic drafting goes (experiment E2). E2's numbers come from T18's three acts and from India Code's footnotes across the 20.

## 2026-11-21 (night): The whole current Constitution parsed (T12, T13, T15; E1 on one document)

**How:** `uv run ingest/pdf.py sources/coi-2026-09-10.pdf out/coi.txt`, then `uv run engine/constitution.py out/coi.txt out/constitution-current`. The source is the Legislative Department's "The Constitution of India (as on 10 September 2026)", 402 born-digital pages. Parsed: pages 32–283, the Preamble to article 395. Not parsed: the Schedules. The output stays in `out/` (git-ignored) and isn't published (T10).

| | Count |
|---|---|
| Articles written as files | 471 |
| Omitted articles (no file; listed in report.json with their notes) | 31 |
| Omitted Parts (VII) | 1 |
| Omitted clauses ("(f)* * * * *"; no line) | 20 |
| Sub-headings ("Right to Equality"; listed, not in files) | 39 |
| **E1, words:** article files whose words equal their source text's, after the stated removals (footnote markers and brackets, omission stars, an omitted clause's label) | **471 / 471** |
| **E1, round trip:** provisions that `structure()` reads back to the same depth and text | **1812 / 1812** |
| Footnotes | 499 |
| … recording a change (substituted, inserted, omitted, added, re-lettered, renumbered) | 477 |
| … of those, instrument found ("ibid." resolved to the one before) | **477 (100%)** |
| … of those, with an in-force date | 461 (the rest: "with retrospective effect", or not yet in force) |
| … of those, not yet in force ("date to be notified", "shall stand substituted") | 18 |
| Other notes (references, judgments, remarks: "See C.O. 41") | 22 |
| Footnotes whose marker wasn't found on its page, or markers without a note | 0 |
| Brackets the source never closes (closed where their article, Chapter or Part ends) | 9 |
| **Against M0:** Preamble, Part III heading and Article 15 byte-identical to the files M0 built by hand | **3 / 3** |
| **Against M0:** footnotes.yaml lines whose footnote the parser links to the same act and section | **8 / 8** |
| Instruments named: Constitution amendment Acts / other Acts / Constitution Orders | 85 / 21 / 1 |
| Substitutions where both the old words (from the footnote) and the new words (in brackets on one line) are known | 109 |

Tests: `tests/test_parse.py`, 13 tests, two of them on the whole PDF (skipped when `sources/` is missing). All 30 tests pass.

**Caveats, so nobody rounds this up:**

- **E1 checks the parser against the extracted text, not the text against an independent copy.** An extraction error passes E1. The only independent check is the M0 cross-check, which covers 2 of 471 articles. Extraction order was wrong on 23 of the 252 pages and is fixed by sorting lines by height (see observations); pages 1 and 336 couldn't be matched and keep pypdf's order (neither is in the parsed range).
- **KICKOFF's T13 asks for a round trip on 30 acts.** This is one document, the biggest, and the parser is Constitution-specific (Parts, Chapters, articles). Acts need sections and Schedules.
- **The round-trip number checks `structure()` against itself:** it shows the files read back stably, not that the nesting is legally right. Known: a proviso after lettered clauses nests under the last clause (contract 2's rule); art. 371A(2)(e) starts "(e) (i) one of the members", so (i) stays inside (e)'s line.
- **The footnote parser was written while reading these footnotes,** so 100% is in-sample. T15's done-when is the three T18 acts, not run yet. "Instrument found" isn't checked note by note; the list of 107 instruments was read by eye.
- **The oath forms in arts. 60, 69 and 159 stack their alternatives** ("swear in the name of God" over "solemnly affirm"). Read in order, the alternative lands mid-sentence: "faithfully execute the office solemnly affirm of President". Every word is there; the layout isn't.
- **Provisions inserted but not yet in force are in the files as printed** (arts. 330A, 332A and 334A by the 106th Amendment, for example), and their footnotes are marked pending in provenance.json.
