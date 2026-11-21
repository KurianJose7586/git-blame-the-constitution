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
