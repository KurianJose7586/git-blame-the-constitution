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
