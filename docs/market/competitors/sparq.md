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

## What they do **not** do

Confirmed absent from their own feature list:

- **Parts marketplace or parts recommendations** → MKT-1, MKT-5, MKT-6
- **Maintenance / service record logging** → MAINT-1, MAINT-2
- **Community or forum-sourced knowledge** → AGENT-1.2
- **Mechanic / shop connection platform** → MKT-3, MKT-8, the ROLE epic

**That list is almost exactly what Wekfest produced evidence for.** See
[`../findings/2026-09-06-wekfest-chicago.md`](../findings/2026-09-06-wekfest-chicago.md):
findings 1 (research and sourcing is the bottleneck), 2 (unobtainable parts, corroborated
three ways), 4 (shops declaring what they want), 5 (MAINT-2 confirmed by someone who sold
three cars privately).

The parts of the roadmap with field evidence are the parts SPARQ has not built. That is
either a real wedge or a shared blind spot; the evidence says wedge, but note that four
conversations is thin.

---

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
