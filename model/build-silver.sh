#!/bin/sh
# M2.md T19: every law's examples from its checked replay, as notes/results.md describes them. Needs the
# git-ignored sources/ and out/ that the T18 replays made. Run from the repository's root.
set -e
G=out/ibc/g; C=out/ibc
uv run model/examples.py out/pocso/silver-2012 out/examples/pocso.jsonl \
  sources/pocso/2013-04-02-criminal-law-amendment-act-2013-s29.txt \
  "out/pocso/cla-2018.txt::Protection of Children from Sexual Offences Act" \
  out/pocso/2019-08-05-amendment-act-2019.txt =out/pocso/current
uv run model/examples.py out/arbitration/silver-1996 out/examples/arbitration.jsonl \
  out/arbitration/2016-01-01-amendment-act-2015.txt =out/arbitration/current \
  out/arbitration/2019-08-09-amendment-act-2019.txt out/arbitration/2021-03-11-amendment-act-2021.txt \
  =out/arbitration/current-2021
uv run model/examples.py out/ibc/code-2016 out/examples/ibc.jsonl \
  $G/2018-01-18-amendment-act-2017.txt $G/2018-08-17-second-amendment-act-2018.txt =$C/consolidated-2018-08-17.txt \
  $G/2019-08-06-amendment-act-2019.txt =$C/consolidated-2019-08-06.txt \
  $G/2020-03-13-amendment-act-2020.txt =$C/consolidated-2020-03-13.txt =$C/consolidated-2020-03-18.txt \
  $G/2020-09-23-second-amendment-act-2020.txt =$C/consolidated-2020-09-23.txt \
  $G/2021-08-12-amendment-act-2021.txt =$C/consolidated-2021-08-12.txt
