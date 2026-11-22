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

## 2026-11-22: The Schedules, a silver history of the whole Constitution, and the parser on an Act

### 1. The whole Constitution, Schedules included (T13, T15)

Same command as above; parsed pages now run to 381, the end of the Twelfth Schedule. Fixed since yesterday: the oath forms now read "swear in the name of God / solemnly affirm"; "(2)(a) There shall be" (art. 239AA, and arts. 6, 112, 233A, 371A) is a clause and its first sub-clause, where before everything after it ran together. Word checks hadn't caught that, because no words were lost.

| | Count |
|---|---|
| Files | 532: 471 articles, 12 Schedules, 48 Part and Chapter headings, the Preamble |
| **E1, words:** article and Schedule files whose words equal their source's | **483 / 483** |
| **E1, round trip:** list items that `structure()` reads back the same, each list on its own | **2760 / 2760** |
| Footnotes | 772 |
| … recording a change, with the instrument found | **732 / 736** (the 4: three state-government notifications and one "s. 74 and Fourth Sch. of" an Act) |
| Brackets the source never closes / closes twice | 27 / 2 (the extra "]" are on pp. 330 and 375) |
| Against M0: Preamble, Part III heading, Article 15 | still byte-identical |

The Schedules' tables (First, Fourth, and the Sixth's table of tribal areas) come out a row per line. Where a "Name" cell wraps ("The Andaman / and Nicobar / Islands"), its pieces interleave with the next column's text: every word is there, but not in reading order.

### 2. A silver history of the whole Constitution, rebuilt from its footnotes

**How:** `uv run engine/rebuild.py out/coi.txt out/constitution-silver.yaml`, then `uv run publish/build_repo.py out/constitution-silver.yaml out/constitution-silver`. Each footnoted change is undone on today's text, newest first. An insertion comes out; a substitution or omission puts back the words its footnote quotes; where it quotes nothing, a bracketed placeholder ("[before The Constitution (Seventh Amendment) Act, 1956, s. 2: not quoted in the footnote]") stands in, so blame is still right. Compound notes ("Ins. by the 38th Amendment … and omitted by the 44th") are two changes.

| | Count |
|---|---|
| Commits (one per section of each instrument) | 441 |
| Changes undone: words put back as quoted / insertions removed / placeholders | 261 / 268 / 242 |
| Changes that couldn't be undone (listed in the report) | 11 |
| **Replayed forwards, the history gives today's text** | **exactly** |
| The rebuilt 1950 text | 393 of 395 articles, Schedules 1–8, 160 placeholders |
| **1950 Article 15 against M0's hand-made one** | **identical** |
| 1950 Preamble against M0's | identical but for one letter: "Unity of the Nation", the footnote's misquote of the 42nd Amendment (observed 21 Nov) |

`git blame` on Article 19 in the result names the First (1951), Sixteenth (1963), Forty-fourth (1978) and Ninety-seventh (2011) Amendments on the right lines.

**Caveats:** silver, not gold, and local only.
- **Placement, not enactment.** Commits sit at in-force dates; the footnotes give no enactment dates, so the trailers say "Enacted: unknown". A change inside another change's brackets is placed after it whatever the dates say: the 70th Amendment changed art. 239AA "w.e.f. 21-12-1991", before the 69th inserted it (1 Feb 1992).
- **Footnotes' words are evidence, not text.** The Preamble's "Unity" shows one misquote; others won't be visible without the amending Acts.
- **What can't be rebuilt.** Art. 238 (Part VII) isn't in today's text at all; the original art. 243 is hidden behind a compound note ("Original Part IX … omitted … Part IX ins. by the 73rd"). Changes noted as "amended in its application to the State of Assam" aren't changes to this text and are skipped.
- **Ordering among same-day changes** follows the Act's year, then nesting, so two changes on one day by Acts of the same year can be swapped.

### 3. The parser on an Act: the RTI Act from DoPT's text

**How:** `uv run engine/constitution.py --act sources/rti-act-dopt-2025-11-18.txt out/rti-act-current`, the text extracted from DoPT's consolidated PDF in T7. Act mode: the preamble runs from "An Act to" to "BE it enacted", Chapters are folders, files are `section-NNN.md`, and parsing stops at the Bill's Statement of Objects and Reasons.

| | Count |
|---|---|
| Files, against M0's hand-built repository | 40 and 40, the same paths |
| E1 words / round trip | 33 / 33, 317 / 317 |
| Footnotes understood | 16 / 17 (the one: "Omitted by G.S.R. 235(E) dated 27-3-2008", which names no Act) |
| Files identical to M0's | 33 of 40 |

The 7 that differ: 5 where M0 follows the Gazette over DoPT on purpose ("expedient", "suo motu", "(24 of 2019)", "thereunder", Second Schedule entries 8 and 27; see tests/official/rti-act/footnotes.yaml), and **2 slips in M0's published files** that the parser gets right: in s. 17 and s. 20, sub-section (1) isn't a list item (s. 20's reads "(1)Where", as DoPT printed it).
