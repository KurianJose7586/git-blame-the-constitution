# Expected results

These are hypotheses and targets, not findings. Revise them after M1, once the baseline's coverage is known, and again after M2. Record actual numbers in `notes/results.md`.

## Metrics

| Metric | Definition |
|---|---|
| Provision exact match (primary) | After the predicted edits are applied, every affected provision's text equals the gold text exactly. Whitespace and punctuation rules are defined once, in `eval/` |
| Edit F1 | Precision and recall of predicted edit operations against gold operations |
| Act-level exact match | The whole act, after all its amendments are applied in order, equals the official current text |
| Validity | Share of outputs that parse and execute |
| Unintended-change rate | Share of outputs that change text the amendment didn't touch (mainly a risk for models that rewrite whole provisions) |
| Cost | GPU-seconds per act, and money per act at a stated reference price |
| Determinism | Share of identical outputs across 5 reruns |
| Verifier recall and false-alarm rate | Measured on deliberately corrupted edits |
| Watcher latency | Time from detecting a new amending act to opening the pull request |
| Linter precision | Share of flags that are correct, on a hand-checked sample |

## Baselines

- The regex baseline from M1
- An open ~70B model, prompted with the edit-language spec and examples, under the same constrained decoding
- A frontier model on at most 100 items, in two modes: rewriting the provision text, and writing edit operations
- Sanshodhan after fine-tuning only, and after fine-tuning plus GRPO

## Experiments

| ID | When | Hypothesis | Test | Success |
|---|---|---|---|---|
| E1 | M1 | The parser represents acts faithfully | Round trip on 30 acts | At least 99% of provisions round-trip exactly |
| E2 | M1 | Most Indian amendment sentences are formulaic | Regex coverage and accuracy | Report both. To verify: a majority is formulaic |
| E3 | M2 | The 1.5B model with constrained decoding and the verifier matches the 70B model at a small fraction of the cost | Provision exact match and cost on IndiaAmend-200 | Equal or better, at 5% of the cost or less |
| E4 | M2 | Rewriting whole provisions drifts on long text; edit operations don't | Unintended-change rate by provision length, rewrite mode against edit mode | Rewrite mode's rate grows with length; edit mode's stays near zero |
| E5 | M2 | The constraints matter | Validity and exact match with and without the grammar and the target-ID rule | 100% validity with constraints, and a measurable exact-match gain |
| E6 | M2–M4 | GRPO with verifier rewards beats fine-tuning alone | Exact match on the hard subset | A gain of several points |
| E7 | M2 | UK data transfers to Indian amendments | UK only, against UK plus Indian silver, against both plus synthetic | Each addition helps on IndiaAmend-200 |
| E8 | M2–M3 | The verifier catches mistakes | Recall on corrupted edits (wrong target, wrong words, a missing edit); false alarms on correct ones | Recall of at least 95%, false alarms of 5% or less |
| E9 | M4 | The watcher is fast | Median time from detection to pull request | 15 minutes or less |
| E10 | M3 | The linter finds real problems | Number of flags, and precision on 200 checked by hand | Precision of at least 90% |

## Targets

| | Minimum (still publishable) | Target | Stretch |
|---|---|---|---|
| Parser round trip | 97% of provisions | 99% | 100% on the Constitution |
| Validity | 99% | 100% | — |
| Provision exact match, IndiaAmend-200 | Regex baseline plus 10 points | 90% | 95% |
| Against the 70B model | Within 5 points | Equal or better | Better by 3 points or more |
| Cost against the 70B model | 10% or less | 5% or less | 2% or less |
| Determinism | 100% with greedy decoding | 100% | — |
| Act-level exact match, 20 acts | 10 acts | 18 acts | 20 acts |
| Verifier recall on corrupted edits | 90% | 95% | 99% |
| Watcher, detection to pull request | 1 hour or less | 15 minutes or less | 5 minutes or less |
| Linter precision | 80% | 90% | 95% |

## If results miss

| Miss | What you can still claim |
|---|---|
| The 1.5B model trails the 70B | Publish the accuracy-against-cost curve across 1.5B, 3B, 7B and 70B. A mid-size model may be the sweet spot |
| Exact match is low on old acts | Report results by era. Born-digital and scanned acts are different problems |
| GRPO doesn't help | Report it. Constrained decoding plus the verifier may already capture most of the gain |
| Coverage falls short of 20 acts | The Constitution alone, fully versioned with blame, is the launch story. Add acts over time |

## Qualitative findings to look for

- Which drafting patterns cause most errors. Likely candidates are references such as "the said clause" or "the proviso thereto", and long substitutions inside Schedules.
- Where Indian drafting is genuinely ambiguous, which shows up as reviewers disagreeing or the model's samples disagreeing.
- How far official consolidated texts lag behind the amendments that change them.

## The headline

If the targets are hit:

> A 1.5B model with a verifier applies Indian legislative amendments with X% provision-level exact match, against Y% for a 70B open model, at Z% of the cost and with identical output on every run. The Constitution and 20 central acts are now on GitHub with full history, kept current by a bot.

Fill in X, Y and Z from `notes/results.md`. Never round in the model's favour.
