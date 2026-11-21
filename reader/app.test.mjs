// node --test reader/app.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { parseRoute, route, versionAt } from "./app.js";

// The Preamble's real dates (the 42nd Amendment was enacted on 18 Dec 1976 and came into force on
// 3 Jan 1977), plus a later amendment whose commencement isn't known.
const law = { commits: [
  { enacted: "1949-11-26", in_force: "1950-01-26" },
  { enacted: "1976-12-18", in_force: "1977-01-03" },
  { enacted: "2023-08-11", in_force: null },
] };
const file = { versions: [{ commit: 0, text: "1950" }, { commit: 1, text: "1977" }, { commit: 2, text: "not notified" }] };
const text = (date, mode) => versionAt(law, file, date, mode)?.text ?? null;

test("as in force on a date", () => {
  assert.equal(text("1950-01-25"), null);
  assert.equal(text("1977-01-02"), "1950");
  assert.equal(text("1977-01-03"), "1977");
  assert.equal(text("2026-11-21"), "1977"); // an unknown commencement is never shown as in force
});

test("as published on a date", () => {
  assert.equal(text("1949-11-26", "enacted"), "1950");
  assert.equal(text("1976-12-20", "enacted"), "1977");
  assert.equal(text("2026-11-21", "enacted"), "not notified");
});

test("routes round-trip", () => {
  for (const h of [
    "#/constitution",
    "#/constitution/part-iii/article-015@2006-01-20",
    "#/constitution/preamble@1950-01-26..2026-11-21?published",
    "#/constitution/preamble?view=blame",
  ]) assert.equal(route(parseRoute(h)), h);
});
