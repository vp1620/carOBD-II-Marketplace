# SPARQ

**Checked 2026-09-08.** OBD-II dongle plus an AI diagnostics app. Shipping today.

Sources: [joinsparq.com](https://joinsparq.com/) ·
[Amazon listing](https://www.amazon.com/SPARQ-Diagnostic-Bluetooth-Compatible-Subscription/dp/B0FTNLTRWS) ·
[MOTOR](https://www.motor.com/2024/11/consumer-device-turns-cars-into-ai-taking-the-guesswork-out-of-car-service-and-maintenance/) ·
[Techlicious](https://www.techlicious.com/blog/sparq-car-dongle-avoid-breakdowns-cut-repair-bills/)

Everything below is from their own marketing and press coverage — **vendor claims, not
independently verified.** Nobody here has used the product.

---

## What it is

| | |
|---|---|
| **Price** | $129 one-time, "$0/month, no subscriptions or extra fees, ever", 2-year warranty |
| **Hardware** | OBD-II dongle, Bluetooth |
| **Platform** | **iPhone/iOS only.** Android "pending" |
| **Coverage** | 2008+ gas, hybrid, diesel. US and Canada. Not EVs |
| **Positioning** | *"the depth and quality of vehicle data comparable to $10,000-plus commercial-grade OBD-II scanners"* |

## Features they claim

- 50,000+ trouble codes, **generic and manufacturer-specific**
- Plain-English code translation
- Health score, 0–100
- AI voice assistant — ask questions about the vehicle in natural language
- **Audio recording to capture vehicle noises**
- Photo-based tire tread depth analysis
- Repair price estimates, regional
- Predictive maintenance timelines with costs
- "Timelapse" — accident history, title records, recalls, previous repairs

---

## Overlap: what they already do that we planned to build

| Our story | Their status |
|---|---|
| **DIAG-1** plain-language codes | shipping, core feature |
| **DIAG-3** manufacturer-specific codes | **50,000+ codes claimed** |
| **AGENT-1.4** cost estimate + urgency | shipping, regional pricing |
| **PRED-1/2** predictive maintenance | shipping, with cost timelines |
| **PRED-8** acoustic anomaly detection | **audio capture shipping** |
| **MOB-2** native app + adapter | shipping, iOS |

**Two of these need a response.**

### DIAG-3 — the hard part is solved, by someone

`BACKLOG.md` says manufacturer codes "are not published the way SAE codes are, so
**sourcing and verifying** them is a bigger gate on supporting BMW than any storage
decision." Someone got to 50,000. Whether the data is any good is unknown, but the gate is
evidently passable, so it is not a moat.

### PRED-8 — the RPM advantage is now **unconfirmed**, not disproven

PRED-8's whole justification is:

> **Our unfair advantage is RPM.** [Order analysis] requires a tachometer signal, which a
> standalone audio app does not have and we already poll.

SPARQ has the mic **and** the OBD port, so the argument that a competitor cannot correlate
the two no longer holds on its face.

**But it is not disproven.** Their public material describes *record a noise → AI
identifies it*, which reads as **absolute classification**, not order analysis. Those are
different techniques: classification asks "what does this sound like?"; order analysis asks
"does this frequency scale with shaft speed?" — which is how a mechanic actually triages by
ear, and which is what needs the tachometer.

**Marked assumed. Worth an hour to check** — if they do not correlate with RPM, PRED-8's
reasoning survives intact and is arguably strengthened by their having tried the easy
version. If they do, PRED-8 needs rethinking before any work starts.

---

## Company

Irvine, CA. Founded by **Codrin Cobzaru and Daniel Nieh** — long-time partners across
previous technology startups, so not first-time founders. Origin story: Cobzaru's partner
was repeatedly over-quoted by mechanics. Launched via Kickstarter.

**Won "Best Tools & Equipment Product" at the SEMA Show 2025.** That is the industry's
largest aftermarket trade show, and it is a meaningful credential — it means the trade,
not just consumers, has looked at this.

Price is inconsistent across sources: **$499 retail** in the launch press release, **$129**
on Amazon and their own site. Either a large discount or a repositioning; unresolved.

## What they do **not** do

⚠️ **This list shrank on 2026-09-08.** See *SPARQ CoLab* below — the shop-connection and
parts claims are already obsolete.

- **Maintenance / service record logging for private resale** → MAINT-1, MAINT-2
- **Community or forum-sourced knowledge** → AGENT-1.2
- **The long tail of parts** — unobtainable, discontinued, fabricated → MKT-5, MKT-6, MKT-7.
  CoLab orders parts through shop supply chains, which is a different problem from *the
  part is not manufactured anymore*.

## SPARQ CoLab — announced, shipping 2026

**This invalidates what this note originally claimed.** CoLab is a shop-facing platform,
and it does most of the mechanic-connection epic:

- drivers **share vehicle diagnostic data remotely** with a chosen service centre
- **repair estimates** with parts costs, labour rates and tax; approve or decline in one click
- **appointment booking**, invoicing, parts ordering — "cradle-to-care", their phrase
- AI summarises the diagnosis so the shop spends less time explaining

**Directly overlapped:** MKT-3 (recommendation flow with a mechanic gate), the ROLE epic,
and the *2026-09-04 decision in `DECISIONS.md`* about what a shop can see — they are
shipping an answer to a question this project has only written down.

**MKT-8 may survive.** Nothing in the announcement says a shop can declare *what work it
wants* versus what it can do. That was single-source evidence from one builder, and it is
now one of the few marketplace ideas here with no visible competitor. Worth confirming with
a real shop before treating it as a wedge.

**That list is almost exactly what Wekfest produced evidence for.** See
[`../findings/2026-09-06-wekfest-chicago.md`](../findings/2026-09-06-wekfest-chicago.md):
findings 1 (research and sourcing is the bottleneck), 2 (unobtainable parts, corroborated
three ways), 4 (shops declaring what they want), 5 (MAINT-2 confirmed by someone who sold
three cars privately).

The parts of the roadmap with field evidence are the parts SPARQ has not built. That is
either a real wedge or a shared blind spot; the evidence says wedge, but note that four
conversations is thin.

---

## The one thing they structurally cannot copy

**Their revenue is the device** — $129 on Amazon, $499 in the launch material. So the
position they cannot take is **"works with the adapter you already own."**

Going device-agnostic would cannibalise the thing they sell. That is the innovator's
dilemma rather than an oversight, which makes it the only durable positional advantage
available here: a competitor cannot follow without dismantling their own business.

Everything else in this note is a gap that could close next quarter. This one cannot.

See `DECISIONS.pending.md`, 2026-09-08. The honest cost is that **adapter compatibility
then becomes the product** — clones report `ELM327 v2.1` while implementing a subset of
v1.5, and *"it does not work"* is unfalsifiable when you do not know what hardware someone
has. Controlling the hardware is exactly why a vendor ships their own.

That promotes OBD-5/OBD-6 from robustness chores to the flagship: every user who hits a
strange adapter makes the next one work, and a hardware vendor structurally cannot build
that asset because they only ever see their own device.

## The strategic read

**SPARQ is a diagnostic product. This is a marketplace with diagnostics as customer
acquisition.** Those are different businesses that happen to share a dongle.

The Wekfest evidence is the clearest statement of the difference: the owner who described
his real process was **already getting the code**. His week went into *which part, from
where, at what price*. SPARQ solves the part he had already solved.

Three things follow.

**1. Our diagnostic layer is table stakes now, not a differentiator.** Building DIAG-1
better than a shipping product with an AI assistant is a race we lose. Build it adequately
and spend the effort on MKT-5 and MAINT-2.

**2. $129 one-time is a price anchor, and "no subscription" is now an expectation** rather
than a positioning choice. Any subscription in this space is priced against free.

**3. Their existence is evidence the problem is real.** A funded product with press
coverage means somebody else believes drivers will pay to understand their car. That is
useful — the risk was never that this problem does not exist.

## Gaps worth noting

- **iOS only, Android pending.** Relevant to #31: Web Bluetooth reaches desktop and
  Android *today*, and Android is the platform they have not shipped.
- **2008+, no EVs.** Older cars are excluded — and older cars are precisely where the
  unobtainable-parts problem (MKT-5) lives.
- **"Comparable to $10,000 scanners" is marketing**, not a measurement. Unverified.

## What would change this assessment

- Buying one and using it. Nobody here has.
- Confirming whether their audio feature correlates with RPM.
- Them shipping a parts marketplace or service-record export — either would remove a wedge.
