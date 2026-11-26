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
| **E1, words:** article and Schedule files whose words equal their source's | **483 / 483** (over the wrong 471 articles until 24 Nov: see there) |
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
| ~~Replayed forwards, the history gives today's text~~ | ~~exactly~~: true by construction, withdrawn 24 Nov |
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
| Files identical to M0's | 33 of 40 (35 after the fix below) |

The 7 that differ: 5 where M0 follows the Gazette over DoPT on purpose ("expedient", "suo motu", "(24 of 2019)", "thereunder", Second Schedule entries 8 and 27; see tests/official/rti-act/footnotes.yaml), and **2 slips in M0's published files** that the parser gets right: in s. 17 and s. 20, sub-section (1) isn't a list item (s. 20's reads "(1)Where", as DoPT printed it).

**Fixed later on 22 Nov:** the 2 slips are corrected in `history/rti-act.yaml` and india-law/rti-act is rebuilt. The parser now differs from M0 only in the 5 deliberate places.

## 2026-11-22 (evening): T18 started on the Insolvency and Bankruptcy Code

**Sources:** 16 PDFs from IBBI's own list (ibbi.gov.in, Legal Framework, Act), downloaded with your approval and listed in `sources/ibc/SOURCES.txt` (not committed): the Code as gazetted, its seven amending Acts (2017 to 2026) and a corrigendum, the J&K Adaptation Order, 2020, and IBBI's consolidated Code after six of the amendments.

### 1. The Code as gazetted, into law files (T12, T13)

**How:** `uv run ingest/pdf.py --gazette sources/ibc/2016-05-28-ibc-2016.pdf out/ibc/g-2016.txt`, then `uv run engine/constitution.py --act out/ibc/g-2016.txt out/ibc/code-2016`. The Gazette prints each section's heading and each cited Act's number in the margin; the extractor runs them in where a consolidated text has them ("2. Application.—", "Companies Act, 2013 (18 of 2013)").

| | Count |
|---|---|
| Sections / Schedules | 255 of 255 / 11, in 5 Parts and their Chapters |
| Margin headings placed | 267 (sections, and sections quoted in the Schedules) |
| Margin citations placed | 48 of 49 (the one: "Indian Penal" / "Code." wraps across lines) |
| **E1, words** / round trip | **266 / 266**, 1916 / 1916 |
| **Independent check:** words of the parse found, in order, in IBBI's consolidated text of 17 Aug 2018 | **53,996 of 54,257 (99.5%)** |

The 0.5% is mostly the 2017 and 2018 amendments themselves ("repaid" became "paid", new clauses), which is what the replay has to produce. Also in it: 10 words the Gazette PDF's text layer runs together ("thecosts", "threemonths"; pypdf's own text has them too), and spelling differences between the Gazette and IBBI ("maximisation"/"maximization", and IBBI's "(XXXVIII of 1939)" for the Chartered Accountants Act, 1949).

### 2. Experiment E2, held out: the regex baseline on the IBC's amending Acts (T16)

**How:** each amending Act extracted with `--gazette`, split into its sections, each section's wrapped lines rejoined into instructions and quoted blocks, then `engine/baseline.py`. The baseline's rules were written on M0's 16 provisions, before these were seen. Repeal-and-savings sections and amendments of other Acts are left out.

| Amending Act | Provisions |
|---|---|
| IBC (Amendment) Act, 2017 (Act 8 of 2018) | 8 |
| IBC (Second Amendment) Act, 2018 | 38 |
| IBC (Amendment) Act, 2020 | 12 |
| IBC (Second Amendment) Act, 2020 | 2 |
| IBC (Amendment) Act, 2021 | 15 |
| **Total** | **75** |
| **Fully understood (operations, nothing missed)** | **38 (51%)** |
| Partly understood | 10 |
| Not understood | 27 |

What the 37 misses need: inserting a whole new section, Chapter or Schedule (12; the executor can't add a file yet); a proviso or Explanation as a node, as in "for the proviso", "before the Explanation", "the Explanation shall be numbered as Explanation I" (10); "the words and figures", "the words, figures, brackets and letter" (7); a clause's block quoted on the instruction's own line (3); "at both the places where they occur" (1); the rest, instructions the rejoining split.

Not counted: the IBC (Amendment) Act, 2019 is a scan with no text layer (OCR isn't built), and the 2026 Act is printed as the Bill as passed, with line numbers that displace its section numbers (". (1)", "Code1"); it needs its own layout handling.

**Caveat:** "understood" means the baseline produced operations and missed no instruction, not that they're right. Whether they're right is the replay against IBBI's consolidated copies, which hasn't run yet. The split into provisions and the rejoining of lines are a script in progress, not committed.

## 2026-11-22 (night): T18's replay on the IBC, 2016 to 2021

**How:** `uv run engine/reconstruct.py out/ibc/code-2016 out/ibc/replay <amending Acts and =checkpoints in order>`. The Code as gazetted, then each amending Act's provisions through the regex baseline and the executor, compared word for word with IBBI's consolidated Code at each of its six dates. The 2019 Act is read by OCR (Tesseract) from its scan; the J&K Adaptation Order, 2020 isn't applied (it amends dozens of Acts at once); the 2026 Act is past the last checkpoint and its Bill layout isn't read yet.

A file "differs only where the Act as gazetted already did" when every difference left is one the unamended 2016 text already had against that consolidation: IBBI's spelling and typesetting ("judgement", "t h e", "co operation"), or its own slips against the Gazette. "New differences" are the rest: the replay's errors, and IBBI departing from the amending Act's words.

| Checkpoint (IBBI) | Files matching word for word | Before any amendment | Amended files | … matching | … differing only where the 2016 text did | … with new differences |
|---|---|---|---|---|---|---|
| 17 Aug 2018 | 201 of 299 | 181 | 44 | 20 | 15 | 9 |
| 6 Aug 2019 | 199 of 299 | 181 | 44 | 18 | 14 | 12 |
| 13 Mar 2020 | 197 of 300 | 179 | 48 | 18 | 15 | 15 |
| 18 Mar 2020 | 196 of 300 | 178 | 48 | 18 | 15 | 15 |
| 23 Sep 2020 | 197 of 301 | 178 | 50 | 19 | 15 | 16 |
| **12 Aug 2021** | **252 of 319** | 210 | **75** | **42** | **10** | **23** |

| Amending provisions | Count |
|---|---|
| Applied in full | 69 of 78 |
| Partly / failed | 5 / 4 |

**Up to 2018, every difference is explained** (the two Acts the T18 test replays, `tests/test_parse.py`):
- *Failed, on purpose:* 2018 Act s. 16, "after the words 'resolution professional'" in s. 22(3)(a), where the words occur three times ("interim resolution professional"); the executor won't pick one. 2018 Act s. 21, "for the word 'seventy-five'" in s. 28(3), where the Gazette's text layer has "seventy five". 2018 Act s. 22(vii), a proviso inside s. 29A's Explanation: contract 2 can't nest a provision under an Explanation, and numbering an Explanation ("shall be numbered as Explanation I") isn't an operation.
- *IBBI departs from the amending Act* (the instrument wins, decision of 21 Nov): "section 7, 9 or section 10" (IBBI drops "section"), "no payment of an unpaid" ("any"), "in specified form, act" (IBBI adds "shall"), "clauses (a) and (c)" ("clause (a) and clause (c)"), "shall form part" ("shall be form part"), "conforms" ("confirms"), "sub-section" ("subsection"), and Act numbers IBBI leaves out ("(12 of 2003)", "(36 of 1963)"). The Gazette's own typo "secton" (2018 Act) is corrected by IBBI.
- *Structure:* s. 2's last clause is followed by unlabelled text ("in relation to their insolvency ..."), which the parser joins to clause (e); substituting (e) drops it. The Gazette's x positions show it (flush left), but the parser doesn't use them.

**From 2019 on, not every difference is checked yet.** The 23 files with new differences in 2021, by first reading: about half are IBBI's (spelling, typesetting such as "t he rem unera tion", Act numbers it omits, "7or" run together in the Gazette's text layer); the rest are the replay's: the OCR'd 2019 Act (two provisions not understood, s. 12 targeted at "(J)" for "(1)", its s. 5 run into s. 4, a clause read as "(6)" for "(b)"), s. 29A's Explanations again, "occurring at the end" (2020 Act, s. 5(15)), the margin headings of two new sections (54H, 54N), s. 208's sub-section, and s. 54A's sub-clause numbering and s. 66, still to look at.

**What it took (held out, so this is the honest cost of the IBC):** the baseline needed whole sections and Chapters, provisos and Explanations as nodes, "the words, figures and letter", "at both the places" (now an `every` flag; without it, words that occur twice are an error rather than a guess), the marginal heading, "for sub-sections (7) and (8)", and context that follows the instruction list's own labels. The executor matches whole words only (before, "payment" would have matched inside "repayment"). M0's replay is unchanged: 12 exact, 13 after quotes, 15 same words.

## 2026-11-23 (night): T18 on the IBC, every difference to 2021 explained

**How:** as on 22 Nov, with the 2019 Act transcribed from its scan (below) and the 2026 Act read from its Bill layout and applied after the last checkpoint.

| Checkpoint (IBBI) | Files matching word for word | Before any amendment | Amended files | … matching | … differing only where the 2016 text did | … with new differences |
|---|---|---|---|---|---|---|
| 17 Aug 2018 | 201 of 299 | 181 | 44 | 20 | 15 | 9 |
| 6 Aug 2019 | 201 of 299 | 181 | 44 | 20 | 13 | 11 |
| 13 Mar 2020 | 200 of 300 | 179 | 48 | 21 | 12 | 15 |
| 18 Mar 2020 | 199 of 300 | 178 | 48 | 21 | 12 | 15 |
| 23 Sep 2020 | 200 of 301 | 178 | 50 | 22 | 12 | 16 |
| **12 Aug 2021** | **259 of 321** | 210 | **77** | **49** | **8** | **20** |

| Amending provisions | Applied in full | Partly | Failed |
|---|---|---|---|
| 2017 to 2021 Acts (83) | **80** | 2 | 1 |
| 2026 Act (71; no consolidation after it to check against) | 56 | 9 | 6 |

**Every difference at the 2021 checkpoint is explained.** Of the 20 files with new differences, 17 differ only where IBBI departs from the amending Act's own words, each checked against the Gazette text or, for 2019, the scan: "initiating" (IBBI "initiation"), "license", "clearances", "arrangements" (2020 Act; IBBI "licence", "clearance", "arrangement"), "having been fulfilled" (IBBI drops "been"), "incharge" (Gazette's text layer; IBBI "in charge"), "under Explanation I" (IBBI adds "the"), "any other law" (2018 Act; IBBI drops "other"), "For the removal of doubts" and "For the purposes" (2019 Act; IBBI drops "the", writes "purpose"), "section 7 or section 9" (2021 Act; IBBI drops "or"), "(ii)", "(iii)" in s. 54A (IBBI renumbers them), "secton" (the 2018 Act's typo, which IBBI corrects), "subsection", "register", "shall be form part", "t he rem unera tion", "fo rce", "1939", and the Act numbers IBBI leaves out ("(12 of 2003)", "(36 of 1963)", "(6 of 2009)", "(18 of 2013)", "(27 of 2006)").

The replay's own differences, all explained:
- **s. 2:** the unlabelled text after its last clause ("in relation to their insolvency ...") is joined to clause (e) by the parser, so substituting (e) drops it. The Gazette's x positions show it is flush left; the parser doesn't use them.
- **s. 66:** "after sub-section (2)" puts the new (3) after the section's closing Explanation, which contract 2 nests under (2); IBBI puts it before. Changing where a closing Explanation nests would change M0's published Article 15.
- **s. 208:** the 2021 Act inserts "after clause (c)" of s. 208, which has a clause (c) in both sub-sections; the executor won't choose.
- **s. 22(3)(a), s. 28(3)** (2018): "after the words 'resolution professional'" matches three places; the Gazette's text layer has "seventy five" where the amendment quotes "seventy-five". These two don't show as new differences, because the 2016 text already lacked the change.

**The 2019 Act, transcribed.** It is a scan. Tesseract reads it but misreads labels ("(6)" for "(b)", "(J)" for "(1)", "(@" for "(i)") and puts margin notes on the wrong lines, because the scan is skewed and the margins overlap the body's x range. So the three pages were read from the page images and typed out, in the extractor's format, into `sources/ibc/2019-08-06-amendment-act-2019.transcribed.txt` (not committed), then compared word for word with Tesseract: they agree except where Tesseract misread a label or dropped a word ("a", "(i)", "(1)"), each checked against the image. All 8 of its provisions apply.

**Held out once more: the 2026 Act.** Read before any rule was written for it, the baseline fully understood **56 of its 71 provisions (79%)**, partly 9, not at all 6, against 38 of 75 (51%) for the 2017 to 2021 Acts before T18's rules. After rules for what it showed (renumbering a clause, omitting several sections or clauses at once, replacing a marginal heading, four sub-sections substituted together, "occurring at both the places"), 64 of 71; 56 of 71 apply in full, with nothing to check them against until IBBI or India Code publishes a consolidation after 2026. What fails: words the Bill's text layer breaks with a space the repair can't decide ("t he", "pro ceeding"), words that occur twice ("period of", "liquidate"), "the long line" and "the opening portion" (no operation for them), a Chapter omitted, and amendments to the 2021 Act's (ca), which wasn't applied.

## 2026-11-23: T18 on POCSO, rebuilt backwards and replayed forwards

**Sources** (`sources/pocso/`, not committed): the Ministry of Women and Child Development's copies of the Act (a scan with someone else's OCR layer, unusable for parsing) and of the POCSO (Amendment) Act, 2019 (a digital Gazette copy); and India Code's consolidated text as of 28 Feb 2023, as hosted by the Jharkhand High Court. Neither the 2012 Act nor the Criminal Law (Amendment) Act, 2013 is in the e-Gazette's index.

**How:** with no clean copy of the Act as enacted, the 2012 text is rebuilt backwards from the consolidated text's footnotes (`engine/rebuild.py`, as for the Constitution), then the 2019 amending Act is replayed forwards on it (`engine/reconstruct.py`) and compared, file by file, with the consolidated text.

| | Count |
|---|---|
| Consolidated text parsed: sections, the Schedule | 47, 1; E1 48 / 48, round trip 221 / 221 |
| Footnotes; change notes understood | 21; 20 / 20 (Act 25 of 2019: 17, Act 34 of 2019: 1, Act 13 of 2013: 1, Act 22 of 2018: 1) |
| Rebuilt 2012 text: changes undone (words put back / insertions removed / placeholders) | 10 / 5 / 5, none lost |
| **Independent check:** words of the rebuilt 2012 text found, in order, in the scan's OCR | **7,318 of 7,664 (95.5%)** |
| **The 2019 Act replayed, held out:** provisions applied in full / partly / failed | **7 / 1 / 2 of 10** |
| Files matching the consolidated text word for word | **53 of 57** (46 before the replay) |

**Every difference is explained:** s. 1 (the J&K Reorganisation Act's omission), s. 42 and s. 42A (the Criminal Law (Amendment) Acts, 2013 and 2018) are instruments not to hand; s. 9 fails because **the 2019 Act misquotes the text it amends**, "communal or sectarian violance" (its s. 6; its s. 4 spells the same words right, and India Code applies both); s. 4 is a placeholder in the rebuilt text, because its footnotes don't quote the old section, and the Act renumbers it "as section 4(1)", an operation the executor doesn't have.

**Caveats:** the base is silver, rebuilt from the same consolidation the replay is compared with, so agreement shows the amending Act's instructions produce what the footnotes record, not that either matches the 2012 Gazette word for word; the 95.5% against the scan is the only independent check of the base. The baseline needed two more things from this Act: "re-lettered", and Roman numerals "(I)", "(II)" as a list of their own.

## 2026-11-23: T18 on the Arbitration and Conciliation Act

**Sources** (`sources/arbitration/`, not committed), found without the e-Gazette: the Tripura High Court's copy of the Act, which is India Code's consolidated text as amended by the 2015 Act only (every footnote cites Act 3 of 2016); and PRS India's copies of the amending Acts of 2015 (Act 3 of 2016), 2019 (Act 33 of 2019) and 2021 (Act 3 of 2021), the same sizes as the e-Gazette's files.

**How:** as for POCSO: the 1996 text rebuilt backwards from the consolidated text's footnotes, the 2015 Act replayed forwards on it and compared file by file; the 2019 and 2021 Acts replayed after it, with no consolidation to check them against.

| | Count |
|---|---|
| Consolidated text parsed: sections, Schedules | 90, 7; E1 97 / 97, round trip 680 / 680; 40 / 40 change notes understood |
| Rebuilt 1996 text: changes undone (words put back / insertions removed / placeholders) | 6 / 16 / 18, none lost |
| **The 2015 Act replayed:** provisions applied in full / partly / failed | **20 / 3 / 2 of 25** |
| Files matching the consolidated text word for word | **102 of 112** (89 before the replay) |
| **Held out, the 2019 Act** (no rule written for it): provisions fully understood | **14 of 15** |
| Held out, the 2021 Act | 1 of 3 |
| The 2019 and 2021 Acts replayed, unchecked: applied / partly / failed | 11 / 1 / 6 of 18 |

**Why the 2015 replay falls short, file by file:** the rebuilt base, not the replay, in most of them. Where a footnote says only "Subs. ..., for clauses (a) and (b)" (s. 37) or "for sub-section (12)" (s. 11), one unlabelled placeholder stands for what was replaced, so a later instruction that names (b) or (12) finds nothing; s. 9's placeholder lands inside its first line, so "Section 9 ... shall be renumbered as sub-section (1)" has no clean paragraph to wrap. And **India Code's footnote misquotes the old words** of s. 11(9), "the Chief Justice of India of India or the person ...", which the rebuilt base inherits, so the 2015 Act's correct quotation can't match (the Constitution's "Unity" again). Checking the base needs the Act as enacted: the e-Gazette's 1996 scan (Gazette ID 48447).

**What the 2019 and 2021 Acts need that the engine hasn't got:** inserting a whole new Part (Part IA, ss. 43A to 43M), so the 2021 Act's substitution of s. 43J has nothing to substitute; omitting a Schedule; "in the long line, for the portion beginning with ... and ending with ...".

New in the engine for this Act: "Section 9 ... shall be renumbered as sub-section (1)" (a RENUMBER of a whole section), "the Explanation to sub-section (2)", a closing double quote typeset as "’’", "(8),the following" with no space, an Explanation of clause (b) found under sub-section (2) where contract 2 nests it, and placeholders that say "Explanation.—" or "Provided that" when the footnote says what they replace. Words the text layer runs together more than once ("Insection", "Providedthat") are split when the separated form is clearly more common; hyphenated words don't count as pairs, so "cooperate" stays whole.

## 2026-11-23: The rebuilt bases checked against the Gazette

You downloaded two files from the e-Gazette by hand: the Arbitration and Conciliation Act, 1996 as gazetted (19 Aug 1996, Gazette No. 54, ID 48447; a scan with a text layer) and the Criminal Law (Amendment) Act, 2018 (ID 188472; digital).

| | Count |
|---|---|
| **Arbitration:** words of the 1996 text rebuilt from India Code's footnotes, found in order in the 1996 Gazette | 14,919 of 21,812 (68.4%) |
| … leaving out the Fifth to Seventh Schedules, which the rebuild didn't remove | **14,912 of 15,760 (94.6%)** |
| POCSO, for comparison: the rebuilt 2012 text against the 2012 scan | 7,318 of 7,664 (95.5%) |

**Why the Fifth to Seventh Schedules are still in the rebuilt 1996 text:** the 2015 Act inserted the Fourth to Seventh Schedules together, and India Code marks them with one bracket from the Fourth Schedule's heading to the end of the Seventh. The parser closes any bracket still open at a Schedule's end (a rule that stopped one note in the Constitution covering 838 lines), so only the Fourth comes out. Without those, the rebuilt base agrees with the Gazette as well as POCSO's does; the remaining 5% is the OCR layer's errors and the 18 placeholders.

**POCSO and the Criminal Law (Amendment) Act, 2018:** its POCSO provision (s. 25, on s. 42) is read correctly, held out, but can't apply: s. 42 was substituted by the Criminal Law (Amendment) Act, 2013 first, and India Code's footnote doesn't quote what it replaced, so the rebuilt 2012 text has a placeholder there. The 2013 Act would fill it. POCSO stays at 53 of 57 files matching.

## 2026-11-23 (late): POCSO's s.42, and the Arbitration Act checked to 2021

Two more sources, downloaded on your yes: the Criminal Law (Amendment) Act, 2013 as gazetted (a scan; the Government of India's copy that UNHCR keeps on ecoi.net), and the Arbitration and Conciliation Act consolidated "up to Act No. 3 of 2021" (WIPO Lex's copy of India Code's text; indiacode.nic.in timed out for you, and India Code doesn't list the 2013 Act).

**POCSO, every instrument replayed:** the 2013 Act's s. 29 (s. 42 replaced by ss. 42 and 42A), the 2018 Act's s. 25 (on s. 42), then the 2019 Act.

| | Count |
|---|---|
| Amending provisions applied | 10 of 12 (the 2013 and 2018 ones both apply) |
| Files matching India Code's consolidated text | 53 of 58 |

The five that differ, all explained: s. 1 (the Jammu and Kashmir Reorganisation Act, not to hand); s. 4 (a placeholder the footnotes can't fill); s. 9 (the 2019 Act's own "violance"); **s. 42**, where India Code has "liable to punishment **only** under this Act", a word none of the three Acts has (the 2013 scan read by eye as well as by two OCRs), and prints Arunachal Pradesh's state amendment inside the section; **s. 42A**, where India Code corrects the Gazette's "additon".

**The Arbitration Act, 1996 to 2021:** the rebuilt 1996 text, the 2015 Act, a check against the 2015 consolidation, the 2019 and 2021 Acts, and a check against WIPO's 2021 consolidation.

| | Count |
|---|---|
| At 2015: files matching | 104 of 113 (was 102 of 112: ss. 29A and 29B, inserted together, are now two files) |
| At 2021: files matching | 84 of 116 (73 before any amendment) |
| … amended files that match, or differ only where the rebuilt 1996 text already did | 26 of 34 |
| 2019 Act: provisions applied | 10 of 14 (1 partly, 3 failed) |
| 2021 Act: provisions applied | 0 of 3 |

The first reading (held out, 21–23 Nov) counted the 2019 Act 14 of 15 understood. With a consolidation to check against, 10 apply cleanly, and one of the 14 was wrong: s. 15 ("Amendment to Act 3 of 2016") omits a section of the 2015 amending Act, and the replay had omitted s. 26 of the Arbitration Act itself. It's now skipped, like any amendment of another Act.

The eight files with differences the replay introduced:

| File | Why |
|---|---|
| s. 12 | The rebuilt 1996 text has one placeholder for sub-sections (1) and (2) (India Code's note doesn't quote them), and the 2015 Act's "after sub-section (4)" insertion is missed; both already at the 2015 check |
| s. 17 | The 2019 Act's "in sub-section (1)" isn't found: in the 2015 Act's text layer, s. 17 as substituted begins "(1)A party", so "(1)" isn't read as a label |
| s. 29A | WIPO's "endeavor" for the Gazette's "endeavour", and a Jammu and Kashmir and Ladakh adaptation printed inside the section |
| s. 31A | WIPO's copy numbers that page's footnotes so that s. 31A stays in s. 31's file: the consolidation's parse, not the replay |
| s. 36 | The 2021 Act's proviso, "inserted and shall be deemed to have been inserted with effect from ...", isn't read |
| s. 37 | WIPO's "takeaway" for "take away" |
| s. 42A | WIPO's "contained by" and "confidentially" for the 2019 Act's "contained in" and "confidentiality" |
| s. 87 | The Gazette's margin citations, "(3 of 2016)", which the consolidation leaves out and replaces once with "(23rd October, 2015)" |

What the baseline can't read, from the 2019 and 2021 Acts: "in the long line, for the portion beginning with ... and ending with ..." (s. 11), a new Part (Part IA, so the 2021 Act's s. 43J has nowhere to go), "shall be deemed to have been inserted with effect from", "the Eighth Schedule ... shall be omitted", and a Schedule's reference "[See section 11 (14)]" read as a target in s. 11. These are M2's hard cases (M2.md); they stay out of IndiaAmend-200 because they've been read.

## 2026-11-23 (night): T19, the task format, and the silver examples

**The format** (`model/examples.py`, M2.md decision 2). Input: the amending provision's heading and text, then `---`, then the law it can touch: every file the provision names outside its quotations, line by line, each line after the ID a target would use (`s.30(2)(a)`, `s.29A(c)/proviso2`), and the headings of the files either side. Output: the operations as JSON, each target rewritten to the ID the law shows (`s.18/explanation` becomes `s.18(1)(g)/explanation`). Each example also lists its targets, the enum constrained decoding would allow. `model/build-silver.sh` builds all three laws from their checked replays.

| Law | Amending provisions | All operations applied | Silver | … every target in the law shown | … round-trip |
|---|---|---|---|---|---|
| IBC, 2016 to 2021 | 83 | 80 | 46 | 46 | 46 |
| Arbitration, 1996 to 2021 | 41 | 34 | 21 | 21 | 21 |
| POCSO, 2012 to 2019 | 12 | 10 | 7 | 7 | 7 |
| **Total** | 136 | 124 | **74** | **74** | **74** |

Silver means the files a provision changed are still there at the next consolidation and have no difference there that the base text didn't already have. That is strict: IBBI's own rewordings ("an" to "any", a dropped Act number) count against the IBC's provisions, which is why 46 of its 80 are silver. Round-trip means the output, parsed back and applied to the law before, gives the law the replay made. **T19's "done when" holds: every silver example round-trips.**

Inputs: median 2,044 characters, 90% under 5,042, one over 16,000 (26,746: an IBC provision naming several long sections). Operations: 30 SUBSTITUTE_WORDS, 29 INSERT_NODE, 19 SUBSTITUTE_NODE, 9 INSERT_WORDS, 7 ADD_AT_END, 5 OMIT_WORDS, 2 OMIT_NODE, 1 RENUMBER.

**What M1 found missing, now in the schema, the executor and the baseline:** inserting a Part (as a Chapter is inserted: a folder beside the Part its first section follows); inserting, substituting and omitting a whole Schedule, several in one block ("the following new Schedules"); "the portion beginning with ... and ending with ..." (a `to` field on word operations, within one line, so "in the long line" needs nothing more); label ranges ("sub-sections (11) to (14)"); a block opened with a double quote typeset as two single ones ("‘‘"). Not added, because no Act read so far has them: "the opening portion", and omitting a Chapter.

**The Arbitration Act to 2021, again** (these numbers replace those above). The comparison with parsed law files had summarised each file by its first 80 characters, so a wrong edit further into a file that already differed went unseen; it now lists the differences word by word, as the comparison with a text always did. That showed two wrong edits that had applied cleanly: the 2019 Act's Eighth Schedule appended to the Seventh's file, and the 2015 Act's Fourth to Seventh Schedules appended to the Third's.

| | Count |
|---|---|
| At 2015: files matching | 106 of 113 |
| 2015 Act: provisions applied | 19 of 24 (s.25's four Schedules now fail: the rebuilt 1996 base already has the Fifth to Seventh, the bracket problem of 23 Nov) |
| 2019 Act: provisions applied | 12 of 14 (s.11's: India Code's misquote in s.11(9) and sub-sections the 2015 replay left out; s.16, because there's no Fourth Schedule to amend) |
| 2021 Act: provisions applied | 3 of 3 |
| At 2021: files matching | 88 of 130 |

The 22 files with new differences at 2021: **ss. 2 and 11**, the 2019 Act's ss. 2 and 3, which aren't in force (WIPO's copy cites only its ss. 4 to 13, and Part IA from 12 Oct 2023), and the 2015 replay's gaps in s.11; **Part IA, ss. 43A to 43M** (13 files), WIPO's text layer drops the dash after most headings, so its parse runs sections together; **s.12**, the base's placeholder; **ss. 29A and 34**, Jammu and Kashmir and Ladakh adaptations printed inside the sections, and "endeavor"; **s.31**, India Code keeps the old Explanation to s.31(8), which explains a clause (a) the 2015 substitution of (8) removed; **s.31A**, WIPO's footnote numbering; **s.36**, a word broken at a line end in the 2015 Act's text ("enforce ment"); **s.42A**, WIPO's "contained by" and "confidentially"; **s.87**, the Gazette's margin citations.

## 2026-11-24: The audit, and what its fixes change

`notes/audit-2026-11-24.md` read all the code and found errors that produce wrong text without an error: 7 in the parser and the rebuild, 3 in the executor and the baseline, and a cross-site scripting hole in the reader. None changes what's published or M0's results. All of the high and medium findings are fixed, each with a test where it can be shown on made-up text; 66 Python tests pass (49 before). What was skipped, and why: P11 (the slider before the first version; a UI change), R17 and R22 (suspected only), R20 (its one case is better as a placeholder), and the half of E19 that would tell a quoted Schedule's "1." from a new section (the Gazette texts' curly quotes don't balance, so counting them can't tell).

**Two claims that couldn't fail.** "Replayed forwards, the history gives today's text: exactly" (22 Nov) is true whatever the undo steps do, because each commit stores the snapshot it was built from. It's withdrawn. The tests now check the rebuilt 1950 text itself: Article 15 and the Preamble against M0's, art. 19's and art. 214's clauses in order, art. 226's clause (7) with its text before 1979, and the 38th Amendment's year. E1 compares each unit with its own stretch of the source, so it couldn't see text in the wrong article. It still reads 483/483, and the 471 articles are now the right ones: the parse matches the Constitution's own list of contents, all 506 entries (471 files, 34 omitted articles, and art. 238).

| The Constitution | Before | Now |
|---|---|---|
| Articles written as files | 471, with 131A, 226A and 228A (omitted in 1977) live, and 124B, 124C and 371-I glued into the articles before them | 471, as the list of contents has them |
| Footnotes / changes understood | 772 / 732 of 736 | 773 / 732 of 736 |
| ... with an in-force date | 714 | 698: the 38th Amendment's notes no longer take the 44th's date |
| Pages with a footnote left unpaired | 0 | 1 (p. 379: the Tenth Schedule's para 8(3), whose note's marker is on the page before; the note was in the text) |
| Silver history: commits / entries | 441 / 175 | 443 / 150 (an Act's sections on one day no longer interleave with another's) |
| ... words put back / insertions removed / placeholders | 261 / 268 / 242 | 267 / 268 / 247 |
| ... changes that couldn't be undone | 11 | 10 |
| ... sections committed later than their date | 25 | 4, all table rows in the First and Fourth Schedules whose brackets the source never closes or whose columns interleave |
| The 38th Amendment placed on | 1979-06-20 | 1975 |
| The rebuilt 1950 text | 393 of 395 articles | 392 of 395: 238 and 243 as before, and 231 (below) |

In the rebuilt 1950 text, art. 19's (f) now sits between (e) and (g) (it was nested under (6) at the end), art. 214 reads (1), (2), (3) once each (it read (3), (2), (3), (2)), art. 226's (7) keeps its text, and arts. 131A, 226A and 228A are inserted in 1977 and gone in 1978. Art. 231 is a gap: one note of the Seventh Amendment covers arts. 230 to 232, and the rebuild used to leave a stray clause with no heading in 231's place; now it leaves nothing, which is honest but still wrong.

RTI 16 of 17, POCSO 20 of 20 and Arbitration 40 of 40 changes are understood, as before. POCSO's rebuilt 2012 text gains one space ("(a)the" read as "(a) the"); the Arbitration Act's 1996 text is unchanged.

**The Arbitration Act at 2021 (these replace 23 Nov's).** WIPO's headings ending ".––" are now read, so Part IA's sections parse apart (97 sections, now 105). At 2021, 99 of 130 files match (88 before) and 11 have new differences (22): Part IA's 13 are down to s.43A; the other ten are those explained on 23 Nov. The 2021 Act's s.3 becomes silver.

**The executor and the baseline.** The fixes made no silver example's input or output change, and no provision changed outcome: 136 provisions, 124 applied, **75 silver** (IBC 46, Arbitration 22, POCSO 7), all round-trip with every target shown. M0's replay is unchanged (12 of 16 exact). What changed is what the executor accepts: every operation is now checked against `ops.schema.json` (fields, types, targets), a target that two provisions share is refused, a proviso's omission no longer takes a sibling clause, letter ranges ("(a) to (d)") are counted and a range the baseline can't count is a miss, and a quoted block holding quoted words isn't cut short. Silver examples go to `out/examples/*.jsonl`, the rest to `*.unchecked.jsonl`.

**Reproducing it.** `uv run model/build-replays.py` rebuilds from `sources/` everything `model/build-silver.sh` reads, and the Constitution's parse and history, in 89 s. Against the `out/` the numbers above came from, it differs in one word: the IBC's 2016 Gazette prints "alongwith" (s.5(8), page 6, checked by eye), which the current extractor splits; `out/` keeps the Gazette's word. `notes/sources.sha256` records every source file's hash (`sha256sum -c notes/sources.sha256`).

**M1's gate is met,** on PLAN's "every difference explained" branch: the IBC to 2021, POCSO to 2019 and the Arbitration Act to 2021 are replayed and checked against consolidations, with every difference explained (23 Nov, and above). No Act matches exactly.

## 2026-11-26: T24, the evaluation harness

`eval/run.py` takes any system (a function from an item's input to the JSON of operations) and scores it on the law it produces (M2.md decision 4): exact match of the files the item carries after the output is applied, the same words, validity, unintended changes (a line the gold leaves alone changed or removed), edit F1 against gold operations where an item has them, determinism over 5 runs, and seconds per item. `model/examples.py`'s records now carry those files, before and after: the files shown and the files the replay changed. M0's hand-written histories are read as items too, with no gold operations.

`uv run eval/run.py regex out/examples/*.jsonl history/*.yaml --by law,silver`:

| law, silver | items | exact | words | valid | unintended | edit F1 | same | s/item |
|---|---|---|---|---|---|---|---|---|
| arbitration True | 22 | 100% | 100% | 100% | 0% | 100% | 100% | 0.001 |
| arbitration False | 12 | 92% | 92% | 92% | 0% | 100% | 100% | 0.001 |
| ibc True | 46 | 100% | 100% | 100% | 0% | 100% | 100% | 0.000 |
| ibc False | 34 | 97% | 97% | 97% | 0% | 100% | 100% | 0.000 |
| pocso True | 7 | 100% | 100% | 100% | 0% | 100% | 100% | 0.000 |
| pocso False | 3 | 100% | 100% | 100% | 0% | 100% | 100% | 0.000 |
| constitution (M0) | 4 | 75% | 100% | 100% | 0% | n/a | 100% | 0.000 |
| rti-act (M0) | 12 | 75% | 92% | 100% | 0% | n/a | 100% | 0.000 |
| all | 140 | 96% | 98% | 99% | 0% | 100% | 100% | 0.000 |

**Only M0's rows are a result.** Every other label is the baseline's own output, so its 100% on them is by construction: those rows check the harness (every silver item reproduces its own after-text from the files it carries), not the baseline. M0's after-texts were written by hand, independently of the baseline, and the harness gives what `engine/replay.py` does: 12 of 16 exact, 15 the same words. They're in-sample, since M1's rules were written on them. The baseline's row by IndiaAmend-200's strata waits for T21, and the UK held-out set's for T22.

**Two items show no law to target.** The IBC's 2021 Act s.8 inserts Chapter III-A after Chapter III of Part II, and the Arbitration Act's 2019 Act s.10 inserts Part IA after Part I. The input shows the files a provision names by section, article or Schedule, and these name only a Chapter or Part, so they show none; the baseline's target (s.54, s.43) is outside the input and the harness counts them invalid. Both are unchecked (`shown` false), so no silver example is affected. T19's input should show the named Chapter's or Part's last section before IndiaAmend-200 is drawn.

Not built yet, and when: money per Act at a reference price with T26, which states one; whole-set numbers reweighted to the held-out Acts' failure rate (decision 3) with T21's strata; act-level exact match stays in `engine/reconstruct.py`.
