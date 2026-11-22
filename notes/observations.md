# Observations

Things noticed along the way: bugs, contradictions, surprises, dead ends. Append as you go. Do not tidy.

---

## 2026-11-21: Sourcing the Preamble and Article 15 (T2)

- **India Code was down** (HTTP 504 on search and on act pages) all afternoon. Used the Legislative Department's consolidated PDF instead: "The Constitution of India [As on 10th September, 2026]", English version. Its footnotes match India Code's style ("Ins. by … (w.e.f. 20-1-2006)"). Re-check `tests/official/constitution/` against India Code itself once it's back.
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

## 2026-11-21: The RTI Act (T7)

- **India Code was still down** (504) in the evening. The current text comes from DoPT, the department that administers the Act: "The Right to Information Act, 2005 [As on the 18th November, 2025]", born-digital, with a list of amending acts and footnotes. The enacted text is DoPT's copy of the Gazette of 21 June 2005, a scan with an OCR layer.
- **What changed since 2005:** three amending acts (RTI (Amendment) Act, 2019 on ss. 13, 16 and 27; J&K Reorganisation Act, 2019 on s. 1(2); DPDP Act, 2023 on s. 8(1)(j)) and six notifications under s. 24(2) on the Second Schedule (2005, two in 2008, 2011, 2016, 2021). 13 commits in all.
- **The 2005 text checks out against the Gazette.** Rebuilt by undoing every change, then compared word by word with the Gazette OCR: 98.3% similar, and every difference read by hand. They're OCR errors ("infaimed", "Inteffigence"), marginal notes and chapter headings in different places, and two typos in DoPT's copy that the Gazette doesn't have: "expendient" for "expedient" in the preamble, and "suomotu" for "suo motu" in s. 4(2). The repository follows the Gazette there.
- **The 2005 Gazette has a typo of its own:** the Second Schedule lists "8. Special Prontier Force." (checked on the page image, not OCR). G.S.R. 319(E) of 2021 replaced the entry, which is why DoPT's footnote brackets only "[Frontier]". A 16-year-old typo in an Act, fixed by notification.
- **DoPT reads s. 44(3) of the DPDP Act as removing the proviso to s. 8(1)(j)** ("information which cannot be denied to the Parliament … shall not be denied to any person"): its consolidated text has no proviso after the new clause (j). Whether the proviso survives is contested (it's part of the challenge in Venkatesh Nayak v Union of India, per a petition synopsis). The repository follows DoPT, and this is worth a line in the write-up: consolidation is itself an interpretation.
- **Notification dates vs. effect.** G.S.R. 347 is dated 28 Sep 2005, but the CAG-hosted copy is stamped as published in the Gazette of 8 Oct 2005, and s. 24(2) gives effect on publication. So: enacted 28 Sep, in force 8 Oct, another two-timeline case. G.S.R. 235(E) is dated 27 Mar 2008 and published 28 Mar 2008. The four later (E) notifications are taken as published on their dates; their copies weren't fetched.
- **The file CIC calls "Notification-DOPT-IISch-Amdt.pdf" is G.S.R. 235(E) of 2008,** not the latest amendment, as the name suggests. NCTE hosts the 2005 and 2008 notifications, but its TLS certificate chain doesn't verify, so nothing was fetched from it.
- **Commencement, read literally.** s. 1(3) brings ss. 4(1), 5(1), 5(2), 12, 13, 15, 16, 24, 27 and 28 into force at once and "the remaining provisions" on the 120th day (12 Oct 2005). Read literally, s. 1 itself is a remaining provision; the repository follows the text. ss. 4 and 5 take 12 Oct as whole files (decision 7). The Schedules commence with the sections that use them (13, 16, 24), or G.S.R. 347 would amend a Schedule not yet in force.
- **Assent dates for the three amending acts come from secondary sources** (1 Aug 2019, 9 Aug 2019, 11 Aug 2023); their in-force dates come from DoPT's footnotes. Fetch the Acts themselves to confirm, and to fill in their amending text, which the commits leave out for now.
- **Chapter titles aren't stored anywhere yet** (the folder says "chapter-iii", the title "THE CENTRAL INFORMATION COMMISSION" is dropped), so the official-text check doesn't cover them.
- **The splitter that turned DoPT's text into section files** is a one-off script (not in the repository). Its hard cases are an early look at M1's parser: "(i)" as a clause after (h) versus a roman sub-clause (decided by whether "(ii)" follows), lists nested inside clauses (s. 2(h)), four-letter labels like "(viii)", and wrapped lines that start with "(3) of section 12".

## 2026-11-21: Publishing (T8)

- Live: the reader at https://kurianjose7586.github.io/git-blame-the-constitution/, and the law repositories india-law/constitution (5 commits, 77 year tags) and india-law/rti-act (13 commits, 21 tags).
- **The builds are deterministic across platforms.** The Pages workflow builds on Linux and prints each law's HEAD, and it matched the Windows build that was pushed: constitution 458b82c, rti-act 6cac3cd. So the force-push-free update path in decision 5 holds.
- GitHub's own blame view of `part-iii/article-015.md` shows the amending act beside each clause, because the commit author is the act (decision 6). No reader needed for the basic demo.

## 2026-11-21 (evening): India Code, re-check and loose ends

- **India Code wasn't down; it moved.** www.indiacode.nic.in now only shows a migration notice; the site is https://indiacode.gov.in, a DSpace 7 repository with a public JSON API (`/server/api/discover/search/objects`, filtered by `act_id` and collection: SECTION, SCHEDULE, PREAMBLE, RULE…). Each section carries its text with footnote markers (`section_page_note`) and its footnotes (`section_footnote`) as HTML. T11 (ingest) could use it instead of scraping pages, but only with written permission: India Code's terms ban automated access (see decisions, 21 Nov, T10). Its search ranks the principal act below related acts (the central CPC is on page 3 of its own name), and it served one 502 during a 140-request run.
- **The official consolidations disagree with each other, and with the law.** Re-checking the RTI Act against India Code, word by word:
  - India Code's s. 8 still has the 2005 clause (j) and no footnote for the DPDP Act, two years after enactment and a year after commencement. DoPT's copy has the change.
  - India Code's s. 13 heading says "Terms of office" (the Gazette and DoPT: "Term"), and it keeps the old "Provided also that…" proviso after the new s. 13(5), which the 2019 Act replaced in full.
  - DoPT adds "(24 of 2019)" twice to the new s. 13(5) and writes "there under" in s. 16(5). The 2019 Act has neither. The repository now follows the Act on both.
  - Everything else is formatting: India Code writes "--" for "—", uses straight quotes and puts spaces before commas.
- **Neither official consolidation has the latest Second Schedule.** G.S.R. 864(E) of 23 Nov 2023 added CERT-In as entry 27 (widely reported; a CIC decision relies on it). DoPT's copy "as on 18 Nov 2025" and India Code both stop at entry 26. Not in the repository yet: it needs the notification's exact wording, from the e-Gazette.
- **Assent dates now come from the Acts themselves,** via India Code: 1 Aug 2019 (Act 24 of 2019), 9 Aug 2019 (Act 34 of 2019), 11 Aug 2023 (Act 22 of 2023). The commits now carry each Act's amending text. India Code marks the 2019 Act "Rep., Act 37 of 2023": the routine repeal of spent amending acts, which leaves its amendments in force.
- **India Code doesn't hold the Second Schedule notifications** as documents (none filed under the RTI Act), and NACIN's 2023 "compendium" of RTI amendments turned out to be office memoranda, not the notifications.
- **The IBC (Amendment) Act, 2017 is Act 8 of 2018** (assent 18 Jan 2018), and India Code titles it "2018". Year in the short title and year of the Act number can differ, so match amending acts by number and year, not by title.

## 2026-11-21 (night): The Second Schedule notifications, read on the e-Gazette

- **All six earlier notifications are confirmed, and there are no others.** G.S.R. 864(E) of 23 Nov 2023 (Gazette Extraordinary No. 681) ends with an official list of every earlier amendment to the Second Schedule: G.S.R. 347 (2005), 235(E) (2008), 726(E) (2008), 442(E) (2011), 673(E) (2016) and 319(E) (2021). That's exactly the six in the repository, so the "2014 notification" one web source mentioned doesn't exist.
- **The e-Gazette search had no CAPTCHA** (Search by Ministry, month and year). Each notification was read in the browser's PDF viewer; the files themselves weren't saved, except 864(E), which you downloaded. Its date fields: "Issue Date" is the Gazette's date, "Publish Date" is when it was uploaded (G.S.R. 442(E) of June 2011 was uploaded in September 2012).
- **Every in-force date holds:** each notification's Gazette issue date matches the date used (8 Oct 2008, 9 Jun 2011, 8 Jul 2016, 4 May 2021). G.S.R. 235(E) is dated 27 Mar and published 28 Mar 2008, and the later notifications' notes cite it as "dated the 28th March": the date of publication, not of signature.
- **Entry 8 contains words no notification enacted.** The 2005 Act printed "8. Special Prontier Force." G.S.R. 319(E) of 2021 says only "in serial number 8 for the word “Prontier”, the word “Frontier” shall be substituted". Yet DoPT's copy and India Code both read "8. Special Frontier Force of the Cabinet Secretariat." The repository follows the instruments: "8. Special Frontier Force." (A corrigendum could explain it; none is listed.)
- **Entry 27 (CERT-In) is now in the repository,** from the notification itself, in force 23 Nov 2023. Both official consolidations still lack it two years on.
- **Punctuation-only differences are noted, not applied.** G.S.R. 726(E) and 673(E) close the quote before the full stop ("26. Strategic Forces Command".), where the consolidations print a full stop on the entry. The repository keeps the consolidated form; it follows the primary text where the words differ.

## 2026-11-21: First engine run (T14, T16, T17)

- **The engine turns an interpretive dispute into a one-line diff.** Applied literally, s. 44(3) of the DPDP Act replaces clause (j) of RTI s. 8(1) and leaves the proviso that followed it; DoPT's consolidated text drops the proviso. A reader could show both readings, labelled, instead of silently picking one. Worth a paragraph in the paper.
- **Indian drafting in M0 needed only seven patterns:** for/after/omit the words, for/after/omit a provision (sub-section, clause, serial number, S.No.), and "the following … shall be added". Notifications number entries "(15)" where the Schedule prints "15.", so the executor converts when the target is a Schedule.
- **Keeping blocks as the amending text's own lines worked:** every block's depth came out right from labels alone, including (6)(a), (6)(b) and the Explanation in Article 15, and the provisos of RTI s. 13(5).

## 2026-11-21 (late): Re-sourcing from the e-Gazette

- The three Acts whose amending text the RTI commits quote are all on the e-Gazette, under the Ministry of Law and Justice (Legislative Department), Part II Section 1: the RTI (Amendment) Act, 2019 (1 Aug 2019, e-Gazette 209696), the J&K Reorganisation Act, 2019 (9 Aug 2019, 210407) and the DPDP Act, 2023 (issued 11 Aug, published 12 Aug 2023, CG-DL-E-12082023-248045). Those listings independently confirm the assent dates; the commits now cite the e-Gazette, not India Code.
- **Not done:** reading the three on the e-Gazette's own viewer. "Search by Bill / Assent / Act" and the ministry search both returned server errors from `ViewPDF.aspx` this time, though the same route worked for the notifications earlier. The quoted wording is the Gazette print as reproduced on India Code; a hand check against the e-Gazette copies is still owed (gate check 13–16 covers the result, not the source).
- India Code also publishes "IndiaCode Legislative APIs" through API Setu (15 GET endpoints: bitstream, browse, collections, communities, search), the same DSpace API the earlier scripts called directly, but with registration and keys. That's the sanctioned route for T11.

## 2026-11-21 (night): Parsing the whole Constitution PDF (T12, T13, T15)

- **pypdf's text comes in drawing order, not reading order.** On 23 of the 252 body pages some lines are drawn out of place: page 252 draws "India." (the end of art. 393) above the Part heading, and several pages draw a footnote first. Each chunk's height is in the PDF, so `ingest/pdf.py` sorts lines top to bottom. pypdf's layout mode is worse: it merges lines ("the charge shall61. Procedure for impeachment").
- **Footnote markers come in seven shapes:** "1[" before bracketed text; "1* * *" for an omission; "1(2)* * * *" for an omitted clause; a superscript glued to a word ("such date4 as", art. 166); one glued to an omitted article's number ("731D. [Saving of laws ...]" is note 7 on art. 31D); runs of the private-use glyph U+F02A ("*" to "****" on one page) for unnumbered notes; and a plain asterisk ("of *Puducherry", "3*[239A.").
- **Numbering slips in the footnotes:** "1 Subs." and "2 Subs." without the full stop, "1.Ins." without a space, and a letter-spaced note: "Art 338A i n s . by the Constitution ( Eighty-ninth Amendment) A c t , 2003". One note number serves two markers in art. 214 ("2(2)* * * *", "2(3)* * * *").
- **Art. 330A's heading ends ".-" with a hyphen,** where every other article has ".—".
- **Nine brackets are never closed.** Art. 81(3)'s proviso ends "census.]]", closing two of the three brackets opened in it.
- **One bracket can span articles:** "Arts. 350A and 350B ins.", "Art. 371D and Art. 371E ins.", and arts. 230 and 231 under one substitution note.
- **A side note beside a footnote:** on printed page 192, "(date yet to be notified)" sits to the right of footnote 1, which also says "w.e.f. 16-4-2026". Both can't be right.
- **18 changes the text describes but which aren't in force,** some for decades: the 44th Amendment's rewrite of art. 22(4)–(7) "shall stand substituted" but was never notified (1978); some 42nd Amendment items are "date to be notified"; the 88th Amendment's s. 2 is "date not notifed" [sic].
- **The PDF is current to 2026:** Kerala is "Keralam" (Kerala (Alteration of Name) Act, 2026), and a note on art. 124 says the Supreme Court now has "thirty-seven" other Judges (Supreme Court (Number of Judges) Amendment Act, 2026). Neither is a constitutional amendment.
- **The parser rebuilt M0's hand-made Preamble and Article 15 byte for byte,** blame included: the first check of M0's files that a person didn't do.

## 2026-11-22: The Schedules, the silver history, and the RTI Act through the parser

- **Word checks miss structure.** "(2)(a) There shall be" in art. 239AA has no space between its labels, so clauses (2) to (8) ran together into one line, and E1 still passed, since no words were lost. Found while rebuilding history, when a footnote's bracket landed in the wrong line. A check that every clause label sits at the start of its own line would have caught it.
- **One note number, two brackets.** "7[Puducherry]" can appear twice on a page with one footnote 7. Undoing it as one span (first bracket to last) wiped out the lines between.
- **Brackets the source opens and never closes get "closed" by a stray "]" far away.** In the Fourth Schedule's seat table one note ended up covering 838 lines, into the Ninth Schedule. No bracket crosses a Part or a Schedule, so one still open there is now treated as never closed.
- **Retrospective dates break date order.** The 70th Amendment changed art. 239AA with effect from 21 Dec 1991, before the 69th Amendment that inserted the article came into force (1 Feb 1992).
- **Compound footnotes carry the Emergency's history:** 35 notes like "Ins. by the Constitution (Thirty-eighth Amendment) Act, 1975 … and omitted by the Constitution (Forty-fourth Amendment) Act, 1978" record a change and its reversal in one line. Read as one change, the history loses both.
- **Typesetting in the Fourth Schedule's table:** "14[1[2[** * * *… *]" opens three brackets and closes one; renumbered rows read "4[3.] Assam"; and the Sixth Schedule has "18.* * * * *" with no space and a note glued to a paragraph number ("21. Autonomous districts" is note 2 on paragraph 1, as "731D." was on art. 31D).
- **The same footnote parser read DoPT's RTI notes** with one exception, "Omitted by G.S.R. 235(E)", which names a notification, not an Act.
- **M0's own RTI files have two formatting slips,** found by the parser, not by a person: s. 17(1) and s. 20(1) aren't list items. Fixed on 22 Nov by rebuilding india-law/rti-act (see decisions).
