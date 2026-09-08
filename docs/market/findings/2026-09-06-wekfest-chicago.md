# Wekfest Chicago — 2026-09-06, Navy Pier

**Four conversations.** Mixed Midwest builds, not one marque — every car was different, which
matters: the findings below held across makes rather than inside one community's blind spot.

**No recordings.** Written from memory the following day, so nothing below is a verbatim
quote unless marked. Where a phrase is in quotes it is a close paraphrase, not a transcript.

**Read the caveats before the findings.** Two of the three strongest signals came from
questions that led the witness, and this is the project's first market data — it is enough
to reorder a roadmap, not enough to bet a go-to-market on.

---

## Who

| | Who | Segment |
|---|---|---|
| **P1** | Custom builder, ~50s, wrenching since 18, sponsored builds and parts | Enthusiast / supply side |
| **P2** | Hosts meets, maintains his own cars, does not mod | **Not in the question bank's segments** |
| **P3** | Modded X5; also owned 3 VWs (2 Golf GTI, Jetta GLI) | Enthusiast / DIY fabricator |
| **P4** | Friend; wants to open a shop and manufacture parts under his own brand | Lead, not evidence |

**Zero working mechanics, zero average owners.** See *What did not get tested*.

---

## Findings

### 1. The bottleneck is research and sourcing, not diagnosis — **strong**

P2 described his actual process for a fault, unprompted:

> code from the OBD reader → look it up on Reddit → check various part stores → decide what to do

**It takes him a couple of days to a week.**

He already gets the code. The days go into working out *which part, from where, at what
price*. That is the most useful single fact from the day, because it is behaviour with a
duration attached rather than an opinion.

**What it means for the roadmap.** `DIAG-1` (plain-language codes) is table stakes, not the
product. The value is in what comes after the code:

- **`AGENT-2`** (RAG over Reddit threads) is *literally the manual step he performs*.
- **`MKT-1`** (parts routed from the fault) is the other half of that week.
- **`AGENT-1`** (RAG over owner's-manual PDFs) — **nobody mentioned a manual, at all.** This
  is evidence against building it first.

⚠️ **Caveat:** the follow-up — *"do you wish all the stores and options were in one spot?"* —
was leading. He said yes. Nobody says no to that. The week-long process is the evidence; the
agreement is not.

⚠️ **Unknown:** what he does at the *end* of that week. Fits it himself, or gives up and
books a shop? That answer decides whether he is a marketplace customer or a referral
customer, and it was not asked.

### 2. Unobtainable parts on underserved platforms — **strong, three-way corroborated**

Three people, three different angles, none prompted into it:

- **P2:** people "scavenge around" for parts on older cars that are not manufactured
  anymore. Named **3D printing *or* welding / fabricating it yourself** as the routes.
- **P3:** prototypes and builds parts himself — cosmetic and some internal — because the X5
  has no support for what he wants.
- **P4:** wants to manufacture for exactly this gap, targeting **BMWs without the aftermarket
  depth that WRX / M5 platforms have**.

**This is the strongest thread of the day**, and better evidenced than the go-to-market
hypothesis the project is currently built around.

**It also reframes `MKT-5`.** The story is written around *3D-printed* parts. P2's framing is
better: the need is **"the part does not exist"**, and the manufacturing method is incidental.
Printing is one supply route; a fabricator is another. Widen MKT-5 from *printed parts* to
**unobtainable parts** and both supply routes fit.

**And it argues against `MKT-2`.** That story names SubiMods and JDM Muscle as first vendors —
established aftermarket for well-served platforms. The gap people described is the opposite:
underserved platforms where the aftermarket is not there. That is where a marketplace has a
reason to exist rather than a crowded shelf to compete on.

⚠️ **Caveat:** P2's 3D comment came after a pitch, so *"good idea"* is soft. The scavenging
observation is the hard part, because it is about what people do.

### 3. Simplicity over feature count — **corroborated, two independent people**

- **P1**, who lives on the expert side: even when a process seems simple *to him*, he has to
  explain it simply. That is the expert blind spot, noticed by an expert.
- **P2**: make it simple and UI-friendly rather than cluttered. He said he would use it
  **in that case** — a conditional, and the condition is the point.

**This cuts against the current backlog.** Eleven epics, and recent design work has been
adding scan animations, dropdowns, acknowledgement flows and 3D views. Two of four people
said the opposite, unprompted.

*Interpretation, not quoted:* Vishvesh read this as Apple's cadence — fewer features,
released refined — versus Android's, where everything exists but has to be found. P2 agreed
with the framing when it was put to him, so treat it as a shared reading rather than his own
words.

### 4. Shops should declare what they *want* to do, not just what they *can* — **new, single source**

P1 on being asked for help by non-car friends: he has to weigh whether he actually wants to
take it on, and often refers them to a nearby shop instead. Asked why — **boredom**. Not
money, not liability, not difficulty. He does not want the boring job.

**Nothing in `BACKLOG.md` models this.** `MKT-3` has a mechanic approval gate and `ROLE-2`
has distinct views, but capability and willingness are treated as the same thing. Technically
a Subaru tuning shop *can* do an oil change. Whether it *wants* one blocking a bay is a
different question, and a naive fault→shop router would send exactly the work they refer away.

**Boredom being the reason makes this easier to build than it would be otherwise.** A
preference is not a negotiation. A shop saying "not brakes, yes turbo work" is protecting its
interest, not conceding margin — so it can be framed as *send me more of what I like*, which
is a benefit rather than an extraction.

**This changes `MKT-4`'s risk profile.** MKT-4 is gated on supply-side adoption, with the note
that *a feature that delights owners can repel mechanics*. Tiering is the mechanism that
resolves that tension: it gives the shop control rather than exposure.

### 5. Private sale is where maintenance records earn their value — **`MAINT-2` confirmed**

P3 sold three VWs. On the difference:

- **Dealership** — "wasn't as bad". Dealers do not need convincing.
- **Private buyer** — needed **records of parts bought** to show service was done, plus
  "a good vibe".

This is the first confirmation of `MAINT-2`'s premise from someone who has actually sold cars,
rather than an assumption in the backlog.

Two refinements it produces:

- **The audience is narrower than the story implies.** MAINT-2 serves *private* sales
  specifically.
- **"A good vibe" alongside the receipts is a design constraint, not a nice-to-have.** Trust
  in a private sale is part evidence and part presentation, so the *report* matters as much
  as the underlying data.

**The framing worth keeping:** a shop's service history is portable and credible; a DIYer's is
a shoebox of receipts. Dealerships and shops have the upper hand today, and the app levels it.

### 6. Mod validation is a use for `PRED-3/4` that nobody wrote down — **new, single source**

P3 collects his own data — cooling stats among them — to check a build is stable **before
committing to it**. His stated reason: mods sourced from Reddit are unvalidated, so a DIY is a
risk he is deliberately measuring.

`PRED-3` (per-PID healthy baseline) and `PRED-4` (anomaly detection) are written for
*predictive maintenance*. This is the same machinery for a different job: **does this build
run hotter than it did before?**

It is an easier sell than predictive maintenance, for two reasons:

- He is **already doing it manually**, so the value is not hypothetical.
- He would have a genuine **before/after baseline by design** — which softens `PRED-6`'s
  readiness gate, since a user validating a mod deliberately captures a clean baseline first.

---

## Lead, not a finding: P4

A friend who wants to open a shop, manufacture custom parts under his own brand, and:

- put his parts on the marketplace, targeting **BMWs and other underserved platforms**
- connect Vishvesh to resources he has
- build an app for his shop, using carOBD as leverage

**Why this is filed separately.** Marketplaces die of empty shelves, and `MKT-6` exists
because recruiting sellers into an empty catalog is the hard side. A volunteer seller is
genuinely valuable. But:

- **The shop does not exist yet.** No inventory, no customers, no track record. The
  commitment that matters is listings, not enthusiasm.
- **"Build his shop's app" is a separate product.** Watch that the leverage does not become
  unpaid work for a friend's business while carOBD has five open PRs, no deploy and no CI.
- **He is a friend.** Friends say yes. It is the weakest form of validation precisely because
  declining is socially expensive.

Pursue it. Do not count it as market evidence.

---

## What did **not** get tested

**The go-to-market hypothesis is exactly as unvalidated as it was before the event.**
`../go-to-market.md` rests on *shops hand out dongles as a retention program*. **No working
mechanic was spoken to.** That is now the single most expensive unknown, and it does not need
an event to fix — two or three shop visits would do it.

**No average owners.** The question bank has segments for average owner (m) and (f); neither
was reached. P2 is the closest and still maintains his own cars. Everyone spoken to was
capable and interested — a biased sample for a product aimed partly at people who are neither.

**P1–P6, the parts-and-3D questions**, shipped in #22 for this event and were not asked
directly. Finding 2 is adjacent evidence, not answers. The double-starred one is still open:
*would you buy a printed part from a stranger, and what would make you trust it?*

**Nobody was asked whether they would pay.**

**P1 was never asked whether he would use it.** He called the idea "genius" after it was
explained — discount that heavily, per this folder's own rule: ask about the past, never the
future. He was reacting to a pitch at a car show, where enthusiasm is free. What he *told*
you is the useful part: he fields friends' questions, weighs whether to help, refers them out.

---

## What this changes

**Reorder, with evidence:**

1. **`AGENT-2` before `AGENT-1`.** P2 does the Reddit search by hand. Nobody mentioned a
   manual.
2. **`MKT-5/6` before `MKT-2`.** The gap is underserved platforms, not more listings for
   well-served ones.
3. **Widen `MKT-5`** from *3D-printed parts* to *unobtainable parts* — printing, welding and
   fabrication are all supply routes to the same need.
4. **Promote `MAINT-2`.** Confirmed by someone who has sold cars privately.
5. **New story needed:** shop tiering — what a shop *wants*, not just what it *can* do.
6. **New note on `PRED-3/4`:** mod validation as a second use, with its own justification.

**Do not change yet:** the go-to-market hypothesis. It was not tested.

**A standing check on scope:** two of four people, unprompted, asked for simpler rather than
more. Worth re-reading before adding the next feature.

---

## Method notes for next time

- **Record, with permission.** Writing from memory a day later loses the verbatim phrasing,
  and this folder's own guidance says the exact words are worth more than the summary.
- **Ask the bank's questions before pitching.** Once the idea is explained, everything after
  is a reaction to it. Two of the four best signals here came before any pitch.
- **Watch for leading questions.** *"Do you wish it were all in one spot?"* has one answer.
- **Four conversations is a real improvement over zero** — and it is four, from one event, in
  one city, with no mechanics and no average owners. Treat the findings as directional.
