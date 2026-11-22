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

## 2026-11-21: The RTI Act (T7)

- **Notifications that amend an Act are commits,** with `instrument: notification` in the history file and an `Instrument: notification` trailer (decided over PLAN's "notes, not commits", so the repository matches the official text). Their in-force date is the date of publication, since s. 24(2) gives effect on publication.
- **Omitted text simply disappears from our files.** No "* * *" placeholders: git shows the omission. The official-text check treats a consolidated copy's placeholders ("7. ***.", "India ***.") and amendment brackets as absent, and rejoins words broken across a line after a hyphen.
- **Where the official consolidated copy and the Gazette disagree on text no amendment touched, follow the Gazette,** and say so in the fixture's notes (two cases in the RTI Act).
- **Fixtures moved from `tests/indiacode/` to `tests/official/`,** since the sources now include DoPT and the Legislative Department.
- **Schedules commence with the sections that use them,** and the literal words of a commencement section win over convention (s. 1 of the RTI Act).
- **The reader cycles eight era colours** (was six); the Second Schedule has seven versions.

## 2026-11-21: Choosing the 20 acts (T9)

**Obtained by scripted access to India Code's API before its terms of use were read (see "Terms of use (T10), and a mistake" below). Kept as aggregate counts only; the fetched data was deleted.** Counted from India Code's own footnotes, through its API (one request every two seconds): for each candidate in PLAN M3, the provisions India Code holds, its footnotes, and the distinct amending acts named after "by" in them ("Subs. by Act 24 of 2019"). The counts are a floor, not a census: India Code's footnotes lag (they cite 2 amending acts for the RTI Act, where there are 3), and ordinances and adaptation orders aren't counted.

| Act | Provisions | Footnotes | Amending acts cited | First–last | Before 1950 | Since 2000 | Changes by notification |
|---|---|---|---|---|---|---|---|
| Code of Civil Procedure, 1908 | 176 | 249 | 38 | 1909–2019 | 23 | 3 | 0 |
| Indian Contract Act, 1872 | 269 | 53 | 11 | 1877–2019 | 7 | 2 | 0 |
| Transfer of Property Act, 1882 | 149 | 174 | 23 | 1885–2019 | 16 | 3 | 1 |
| Negotiable Instruments Act, 1881 | 156 | 70 | 21 | 1885–2018 | 12 | 3 | 0 |
| Specific Relief Act, 1963 | 49 | 22 | 3 | 1964–2019 | 0 | 2 | 0 |
| Limitation Act, 1963 | 33 | 25 | 3 | 1969–2019 | 0 | 1 | 0 |
| Hindu Marriage Act, 1955 | 37 | 55 | 9 | 1964–2019 | 0 | 4 | 0 |
| Representation of the People Act, 1951 | 205 | 348 | 39 | 1951–2021 | 0 | 14 | 0 |
| Motor Vehicles Act, 1988 | 259 | 256 | 8 | 1988–2026 | 0 | 6 | 0 |
| Prevention of Corruption Act, 1988 | 35 | 32 | 3 | 2014–2019 | 0 | 3 | 0 |
| Arbitration and Conciliation Act, 1996 | 114 | 53 | 3 | 2016–2021 | 0 | 3 | 0 |
| Foreign Exchange Management Act, 1999 | 52 | 28 | 4 | 2015–2019 | 0 | 4 | 0 |
| Information Technology Act, 2000 | 129 | 131 | 4 | 2002–2023 | 0 | 4 | 5 |
| Prevention of Money-Laundering Act, 2002 | 82 | 125 | 9 | 2005–2019 | 0 | 9 | 0 |
| Right to Information Act, 2005 | 33 | 6 | 2 | 2019–2019 | 0 | 2 | 0 |
| Protection of Children from Sexual Offences Act, 2012 | 48 | 24 | 4 | 2013–2019 | 0 | 4 | 0 |
| Companies Act, 2013 | 534 | 459 | 6 | 2015–2020 | 0 | 6 | 12 |
| Insolvency and Bankruptcy Code, 2016 | 294 | 118 | 6 | 2018–2021 | 0 | 6 | 1 |
| Central Goods and Services Tax Act, 2017 | 191 | 252 | 14 | 2017–2025 | 0 | 14 | 0 |
| Consumer Protection Act, 2019 | 107 | 2 | 1 | 2021–2021 | 0 | 1 | 0 |

What it says about M3:

- **Three tiers of difficulty.** The four colonial-era acts (CPC, Contract, Transfer of Property, Negotiable Instruments) carry 58 pre-1950 amending acts between them, so scans and OCR. The Representation of the People Act has the most amending acts (39) but all after 1950. Everything enacted since 1988 is amended only by born-digital acts.
- **Notifications matter beyond the RTI Act.** The Companies Act (12 footnotes), the IT Act (5) and the IBC (1) have changes made by notification, so the `Instrument` path from T7 will be needed in M3.
- **Born-digital, checked on samples:** India Code's copies of the IBC (Amendment) Act (Act 8 of 2018) and the POCSO (Amendment) Act, 2019 have full text layers.
- **The list of 20 stands as drafted in PLAN.** None is missing from India Code; the Consumer Protection Act, 2019 has barely been amended (1 act) and could make way for a busier act if M3 needs one.

**M1's three reconstruction acts (recommended, to confirm at the start of M1):** the Insolvency and Bankruptcy Code, 2016 (6 amending acts, 294 provisions), the POCSO Act, 2012 (4 amending acts) and the Arbitration and Conciliation Act, 1996 (3 amending acts, including the large 2015 rewrite). All their amendments date from 2013 on, so the engine and baseline get tested on clean digital text first, as PLAN's risk table advises; the colonial acts come in M3.

## 2026-11-21: The primary text wins on words, not on punctuation

Where an official consolidation disagrees with the instrument that made the change (the Gazette, the amending Act, the notification), the repository follows the instrument when the words differ: "(24 of 2019)", "thereunder", "of the Cabinet Secretariat", entry 27. Where only punctuation differs (a full stop inside or outside the closing quote), it keeps the consolidated form and notes the difference. Every deviation from the official fixture is listed in that fixture's footnotes.yaml.

## 2026-11-21: Starting M1

- **Decision 9 confirmed: edit operations are JSON.** One object per operation, `{"op": ..., "target": ...}`, described by `engine/ops.schema.json`; the same schema will drive constrained decoding in M2.
- **M1's three reconstruction acts confirmed:** the Insolvency and Bankruptcy Code, 2016, the POCSO Act, 2012 and the Arbitration and Conciliation Act, 1996.
- **One `engine/` folder instead of PLAN §6's `parse/`, `dsl/` and `baseline/`.** They're a few hundred lines between them and change together; split them when one grows.
- **A block is the amending text's own lines, not our Markdown.** `SUBSTITUTE_NODE` and friends carry the inserted provisions verbatim, one provision per line, and the executor works out depth and formatting. The model in M2 only has to copy text, never indent it.
- **Targets are written the way lawyers cite them**, with the file's own short form: `art.15(4)`, `s.13(5)`, `s.8(1)(j)`, `sch.2(8)`, `preamble`; unlabelled provisions as `s.13(1)/proviso`, `s.13(2)/proviso2`, `art.15(6)/explanation`.

## 2026-11-21: Terms of use (T10), and a mistake

**What the sources say** (read on 21 Nov 2026):

- **India Code** (indiacode.gov.in). Terms of Use, updated 22 Jun 2026: you may "access, download, and print materials ... for personal, non-commercial use only", keeping notices; users must "Not use any automated means to access the Portal for any purpose without our express written permission". Copyright Policy, same date: the Legislative Department claims all content (legislative texts, amendments, annotations, metadata, databases, APIs), and prohibits without prior written permission "copying, reproducing, republishing ... or distributing any content", derivative works, and using API data "for unauthorized purposes".
- **Legislative Department** (legislative.gov.in), where the Constitution text came from: material "may be reproduced free of charge after taking proper permission by sending a mail to us", reproduced accurately, not misleadingly, with the source acknowledged.
- **e-Gazette** (egazette.gov.in): only a liability disclaimer. Nothing restricts access or reproduction.
- **DoPT** (dopt.gov.in), where the RTI Act text came from: its copyright page didn't load. The site runs on the same government template as the Legislative Department's, so the same permission-by-email rule is likely. Unverified.

**The mistake.** India Code's API was queried by script before these terms were read: the RTI re-check, the T9 counts and three amending-act PDFs, about 200 requests on 21 Nov. KICKOFF put T10 first for exactly this reason. Automated access to India Code has stopped and won't resume without written permission.

**What it changes:**

- **T11 as planned (an automated India Code ingester) is blocked** until the Legislative Department grants written permission.
- **Published content that came from India Code:** the amending text in the RTI repository's commits for the 2019 Act (ss. 2–4), the J&K Reorganisation Act (entry 95) and the DPDP Act (s. 44(3)), with their source links; and the T9 counts above. The same Acts are in the Gazette, so they can be re-sourced from the e-Gazette.
- **The copyright question PLAN §8 parked is now pressing,** because M0 is public. Section 52(1)(q)(ii) of the Copyright Act, 1957 makes reproducing an Act non-infringing only "together with any commentary thereon or any other original matter". Whether commit trailers, notes and the reader count is a question for the law-faculty contact, not something to settle here.

## 2026-11-21: API Setu needs an organisation

API Setu's consumer sign-up (Partners portal, "Organization set-up") requires an organisation type (industry and private sector, central or state government), a GSTN or similar ID, an organisation website and an email on the organisation's official domain. Its help assistant said individuals can register, but the form says otherwise. Registering the university ourselves without its authority would misrepresent who is asking, so the options are: the university (through the mentor or department) registers with a staff member or us as its contact, or API Setu waits until M3. M1 uses the e-Gazette and hand-downloaded PDFs either way.

## 2026-11-21 (night): Parsing the consolidated Constitution (T13)

- **Chapters are folders inside their Part:** `part-v/chapter-i/article-052.md`. A file's ID is still its name (`art.52`), and the reader already groups files by folder, titled from each README.
- **Sub-headings ("Right to Equality") aren't in the law files.** Contract 2 has no place for them; report.json lists them. Revisit if the reader should show them.
- **Omitted articles, Parts and clauses get no file or line.** report.json keeps them with their notes. In the history, an omitted article is a deleted file.
- **Footnote markers and their brackets come out of the text,** and provenance.json maps each footnote to the lines it covers. Brackets that belong to the text stay: art. 368(4) "[whether before or after the commencement of section 55 ...]".
- **Provisions inserted but not yet in force stay in the files, as printed,** and their footnotes are marked pending. The history will need an in-force date for them that doesn't exist yet.
- **The parser is `engine/constitution.py`,** following the one-folder decision above, and it's Constitution-specific; a general act parser comes with T18. The footnote parser is `ingest/footnotes.py`, where KICKOFF puts it.
- **Nothing parsed from the Constitution PDF is published** until the Legislative Department's permission or the legal opinion arrives (T10).

## 2026-11-22: Schedules, silver history, Act mode

- **Schedules are one file each,** `schedule-7.md`, headed as printed ("FIRST SCHEDULE", or "THE FIRST SCHEDULE" in an Act). Their headings ("PART A", "List I—Union List", "[Article 244(1)]", a form's number "III") are plain lines, and each run of entries between headings is its own list. A table is a row per line, leaders kept.
- **The engine tells "2." from "(2)".** A Schedule's paragraph "2." and its sub-paragraph "(2)" were the same kind of label to `structure()`, so paragraph 2 nested under sub-paragraph (1). Not in Schedule mode, "N." labels are now their own kind. M0's builds are unchanged (same hashes), and the engine tests pass.
- **A clause that opens with its sub-clause is split:** "(2)(a) There shall be" becomes "(2)" and "(a) There shall be", so `art.239AA(2)(a)` can be cited. The engine reads a label standing alone.
- **Oath forms read "swear in the name of God / solemnly affirm"**, spaced as M0's RTI Act already has it.
- **Silver histories are separate from gold ones.** `engine/rebuild.py` writes `out/constitution-silver.yaml`, never `history/`. The builder takes two optional fields for them: `placed` (the date an act is placed at when its enactment date is unknown; the trailer says "Enacted: unknown") and `footnotes` (the commit body when there's no amending text). A `note` in the history goes into the repository's README. M0's histories build exactly as before.
- **A placeholder stands in for words no footnote quotes,** in square brackets and naming the change, so blame is right even where the old words aren't known. Placeholders aren't law and keep the history silver.
- **Act mode is the same parser,** `--act`: Constitution-specific only in where it starts and what it calls things. The three T18 Acts go through it when their PDFs arrive.
- **M0's two RTI slips (ss. 17(1) and 20(1)) are left as published** until you decide to rebuild india-law/rti-act; fixing them changes every commit's hash.
- **Later the same day: fixed and rebuilt.** Sub-section (1) of ss. 17 and 20 is now a list item, with s. 20's provisos under it, and india-law/rti-act was force-pushed (`--force-with-lease`). The first commit keeps its hash; the other 13 and the year tags from 2005 on change. The word check reads a label glued to its word ("(1)Where", as DoPT and the official copy print it) as two words.

## 2026-11-22: API Setu dropped

- **API Setu is dropped.** Its sign-up needs an organisation (21 Nov), and you judged that unworkable. Nothing in M1 depended on it.
- **Sources stay as T11's revision has them:** the e-Gazette, whose terms don't restrict access or reproduction, and PDFs you download by hand into `sources/`, one CAPTCHA each. India Code is read by script only with the Legislative Department's written permission.
- **The Legislative Department's own site isn't a substitute.** Its Terms of Use (last updated 16 Jul 2025, read 22 Nov) are a disclaimer with no ban on automated access, but its Documents section holds the Constitution, lists of central Acts, ordinances, regulations and repeal lists, not the Acts' texts.
- **What it costs later, to decide at M3:** the 20 acts cite at least 211 amending Acts (T9's table), all to download by hand; 93 belong to the four colonial-era acts, 58 of them from before 1950. Without those four, about 135 PDFs with the principal Acts. The Gazette watcher needs a feed without a CAPTCHA; the fallback is a pull request opened when a new Gazette PDF lands in `sources/`.
- **Both permission emails went out on 21 Nov,** the Legislative Department's still asking about API Setu (its point 2). It went to India Code's support desk; a forward to legislative.gov.in's Web Information Manager, the address its Contact Us page gives for the website, withdraws point 2 (`permission-requests.md`, request 3). The API Setu sign-up steps are gone.
