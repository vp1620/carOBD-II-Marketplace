# Market

How this product reaches people, and what we have actually verified about whether they
want it. Separate from `BACKLOG.md` (what we would build) and `DECISIONS.md` (why the
code is the way it is) — this folder is about **demand**, not supply.

| File | What it holds |
|---|---|
| [`go-to-market.md`](go-to-market.md) | How the product reaches customers, and the open questions in that plan |
| [`validation-questions.md`](validation-questions.md) | Question bank for talking to real people at events |
| `findings/` | What people actually said. One file per event. **Empty until Wekfest Chicago, Sun 6 Sep 2026.** |

## The rule for this folder

**Mark every claim as verified or assumed.** A go-to-market plan full of confident
untested assertions is worse than no plan, because it feels like knowledge.

Today almost everything here is assumed. The `findings/` directory is what turns
assumptions into facts, and it is empty — which is the single most important thing to
know about this project's market understanding.

## `competitors/`

One file per competitor. Answers two questions only: **what do they already do that we
planned to build** (those stories stop being differentiators), and **what do they not do**
(that is where the wedge is, if the field evidence agrees).

- [`competitors/sparq.md`](competitors/sparq.md) — OBD-II dongle + AI diagnostics, $129
  one-time, shipping. Overlaps DIAG-1, DIAG-3, PRED-1/2/8 and AGENT-1.4. Does **not** do
  parts, service records, forum knowledge or shop connections — which is almost exactly
  what the Wekfest findings support.
