# Phase 2 — the part people actually asked for

**Status: evidenced, not committed.** These three epics are here because
[`../docs/market/findings/2026-09-06-wekfest-chicago.md`](../docs/market/findings/2026-09-06-wekfest-chicago.md)
produced evidence for them, and because the SPARQ competitor note (`docs/market/competitors/sparq.md`, pending in #38)
shows a shipping product that does **none** of them.

That combination is the whole argument for this phase: **demand with no incumbent.**

The diagnostic layer that Phase 1 builds is table stakes — SPARQ ships it with an AI
assistant for $129. This is where the product stops being a better scanner and starts
being something else.

---

## Exit criteria

| # | Criterion | How you know |
|---|---|---|
| 1 | Someone finds a part faster through this than by hand | measured against the *days to a week* an owner described |
| 2 | A maintenance record is used in a real private sale | one seller shows it to one buyer |
| 3 | The agent cites where an answer came from | it names its sources and why it chose them |
| 4 | Supply exists before the seller flow does | a catalog with entries, from MKT-6 |

Criterion 1 is the one that matters. **The bottleneck an owner described was research and
sourcing, not diagnosis** — so if this phase does not measurably shorten that week, it has
not worked, however many features shipped.

**What would falsify this phase:** if further conversations show people source parts fine
and rarely hit an unobtainable one, MKT-5/6/7 should stay unscheduled. Four conversations
is thin evidence, and the honest response to thin evidence is to gather more before
committing, not to build faster.

---
### EPIC: Agentic Diagnosis

**Two agents, not six.** IDs are `AGENT-<agent>.<story>`: the first number says *which
runtime component owns the story*, the second is a stable handle. **Priority is the order
stories appear in, not the number** — `AGENT-1.2` is listed first because it is built first.

| Agent | Does | Stories |
|---|---|---|
| **1 — Diagnostic** | retrieval and answer | 1.1 manual RAG · **1.2 forum/Reddit RAG** · 1.3 escalation · 1.4 cost + urgency |
| **2 — Social posting** | posts a question, tracks replies back into the knowledge base | 2.1 reply ingestion · 2.2 blog fallback |

Renumbered from flat `AGENT-1..6` on 2026-09-08. The old scheme implied a grouping that did
not exist and collided with the README's *"Agent 1"* / *"Agent 2"*, which name components —
so `AGENT-3` read as "Agent 1 escalates to Agent 2" with both meanings in one line. Old →
new: 1→1.1, 2→1.2, 3→1.3, 6→1.4, 4→2.1, 5→2.2. All references updated in the same commit.

*(Ordering revised 2026-09-06 from field evidence — see `docs/market/findings/2026-09-06-wekfest-chicago.md`, finding 1.)*
- **AGENT-1.2** — RAG over scraped Reddit threads (Qdrant + MongoDB raw store). **Build this first.**
  - **Why it leads:** an owner described his real process for a fault — read the code, *look it up on Reddit*, check part stores, decide — and put it at **days to a week**. AGENT-1.2 automates a step someone is already performing by hand. The diagnosis is not the bottleneck; the research is.
  - **The corpus is not a given — routing to the right source is most of the work.** "Scraped Reddit threads" quietly assumes a source list exists. It does not, and picking it wrong makes the retrieval worse than a plain web search.
  - **Route by engine/platform, not by badge.** Enthusiasts organise around drivetrains: an EJ25 head-gasket thread is relevant to a WRX, a Forester XT *and* a Legacy GT because they share the engine. Model alone is too narrow and make alone too broad. Note this needs one level deeper than DIAG-3's VIN-derived make — engine and platform come from the fuller decode (MKT-5's fitment problem), so the two share a dependency.
  - **Three tiers, and which one applies depends on the code:**
    - *Platform* — r/WRX, r/E90, r/GolfGTI. Highest signal, narrowest.
    - *Make-wide* — r/subaru, r/BMW. Broader, noisier.
    - *Generic mechanical* — r/MechanicAdvice, r/AskMechanics, r/Cartalk. Where a P0420 is explained with no make context at all.
    A generic SAE code is answered well in the third tier. A manufacturer-specific `P1xxx` code is answered **only** in the first two. That is the same generic-vs-manufacturer split DIAG-3 already makes for the catalog — the same fact surfacing in a second system, which is a good sign the split is real.
  - **Reddit is one source, not the corpus.** Marque forums often have deeper archives and better-preserved threads — NASIOC for Subaru, Bimmerforums for BMW, VWVortex. The story name says Reddit; the design should not assume it.
  - **The source list is data, not code.** Communities move, subs go private, new platforms appear. A hardcoded list rots with no owner. Same treatment as `dtc_zones.json`: a `sources.json` mapping platform → sources, so a revision is a reviewable diff rather than an edit to the file that also holds the retrieval logic.
  - AC: given a code and a vehicle, the agent can name **which sources it searched and why** before it returns an answer. If it cannot explain the routing, the routing is not testable.
- **AGENT-1.1** — RAG over owner's-manual PDF chunks (Qdrant). **Demoted.**
  - **Why:** nobody at Wekfest mentioned an owner's manual, at all. A manual answers service intervals and tire pressures; it does not explain a P0302. Build it when there is demand for what it actually contains.
- **AGENT-1.3** — escalation between the two when confidence is low.
  - **The direction in the original story is backwards.** It had AGENT-1.1 escalating *to* AGENT-1.2 — manual first, Reddit as fallback. Finding 1 suggests Reddit is the primary source for fault diagnosis. Revisit which way the escalation runs before building it.
- **AGENT-2.1** — Background job polls Reddit replies, embeds them, feeds the knowledge base.
- **AGENT-2.2** — Blog fallback after 72h with no reply; notify platform mechanics.
- **AGENT-1.4** — Agent output includes **cost estimate + urgency** (the enthusiast "don't get ripped off" value prop).

### EPIC: Marketplace
- **MKT-1** — Region/zone-aware parts catalog routed from the DTC body zone.
- **MKT-2** — SubiMods + JDM Muscle integration (API/scrape) as first vendors. **Demoted 2026-09-06.**
  - These are established aftermarket vendors for **well-served** platforms. The gap people actually described is the opposite — see MKT-5. Listing more parts for a WRX competes on a crowded shelf; the underserved platforms are where a marketplace has a reason to exist.
- **MKT-3** — Recommendation flow: `source` (agent|mechanic), mechanic approval gate, customer accept → book/order.
  - A share (ROLE-4) sent to a mechanic can carry **the parts the owner was already considering**, so the conversation starts from "here is what I was looking at" rather than a cold diagnosis. The mechanic replies with what they actually have **at that location** — availability is local, not catalog-wide.
  - Customer-supplied parts are deliberately **not** part of this flow — see MKT-4.
- **MKT-5** — As an Enthusiast, I want to buy **parts that are not sold anywhere** — discontinued trim, obsolete brackets, anything for a platform the aftermarket skipped — so a part being unavailable stops meaning the car stays broken.
  - AC: parts indexed **by vehicle fitment**, not keyword; listing states how it was made and from what; a buyer can see which vehicles the maker has confirmed it on.
  - **Evidence** (`docs/market/findings/2026-09-06-wekfest-chicago.md`, finding 2 — corroborated three ways): one owner "scavenges around" for parts on cars nobody manufactures anymore; one fabricates his own because his X5 has no support; one wants to manufacture for exactly that gap, targeting BMWs without WRX-level aftermarket depth.
  - **Not "3D-printed parts".** That was the original framing and it is too narrow. The need is *the part does not exist*; the manufacturing method is incidental — printing, welding and fabrication are all routes to the same gap. Framing it by process would have excluded the person who was already fabricating by hand.
  - Why fitment is the moat: it is the reason generic marketplaces fail at car parts. "Does this fit my 2018 WRX?" is unanswerable on Etsy. We already know the vehicle (STORE-3, VIN-derived make in DIAG-3) and the failed zone (MKT-1), so the routing that is hard for everyone else is routing we already do.
  - Cold start is smaller here than for most marketplaces: **the diagnostic side is the customer acquisition.** Demand arrives with intent already attached rather than being bought.
  - **Safety boundary — a design constraint, not a policy note.** Structural, braking, steering, restraint and fuel-system parts are off the platform. A trim clip and a suspension bracket are different risk classes and must not be the same listing type. Decide the allowed-category list before the first listing exists.
  - Cross-check against **MKT-4**: a shop may refuse to fit a customer-supplied fabricated part on liability grounds, which makes MKT-4's "will you fit supplied parts" filter necessary rather than optional.
  - Depends on **STORE-3** (fitment) and **MKT-1** (zone→part routing).
- **MKT-6** — As a Dev, I want to **find the people already making these parts** and index what they make against vehicle fitment, so the catalog has supply before a single seller is signed up.
  - AC: a pass over Printables, Thingiverse, Etsy and marque forums produces candidates with a proposed fitment; **every entry is human-confirmed before listing**; the maker is contactable.
  - Why before MKT-5's seller flow: supply is the hard side, and aggregating what exists is cheaper than recruiting into an empty marketplace. It also tells you whether the supply exists at all before building tooling for it.
  - Why an agent genuinely fits: reading unstructured listings and inferring *which car does this fit* is a language problem. Failure mode is severe — **a wrong fitment inference sells someone a part that does not fit** — so inferred fitment is a draft for a human, never a published fact. Same guardrail as DIAG-3.
  - Legal: indexing and linking is not relisting. Licences vary and many are non-commercial. Check per item; contact makers rather than scraping them into a storefront.
- **MKT-7** — *(exploratory — do not schedule)* As a Dev, I want to **generate the model for a part we own**, turning a marketplace that takes a cut into a manufacturer with a catalog.
  - **Be honest about what is possible.** Text-to-CAD is not there — you cannot prompt "intake bracket for a 2018 WRX" and get something that bolts on. Dimensional accuracy from a description is the unsolved part, and 2mm out is scrap.
  - The tractable version is **scan-to-CAD**: a phone LiDAR or photogrammetry capture of the broken part, with the model doing mesh cleanup and parametric reconstruction. The bottleneck is *measurement*, not generation.
  - The flywheel: every fault routing to a part we cannot source is a signal for what to model next. Unfulfilled demand is the modelling backlog, and we are the only ones who can see it.
  - Owning the model means owning the liability. MKT-5's safety boundary applies with **more** force — a marketplace can point at the seller; a manufacturer cannot.
- **MKT-8** — As a Mechanic, I want to declare what work I **want**, not just what I *can* do, so I am sent jobs I actually want and not the ones I would refer away.
  - AC: a shop marks service categories as wanted / accepted / declined; the fault→shop router respects it; declining a category is not visible to customers as a rejection, only as an absence.
  - **Evidence** (`docs/market/findings/2026-09-06-wekfest-chicago.md`, finding 4): a builder described weighing whether to help friends with simple jobs and referring them to a nearby shop instead. Asked why — **boredom.** Not money, not liability, not difficulty.
  - Nothing here modelled this: capability and willingness were treated as the same thing. A Subaru tuning shop *can* do an oil change; whether it wants one blocking a bay is a different question, and a naive router sends exactly the work they refer away.
  - **Boredom being the reason makes this cheap to build.** A preference is not a negotiation. Framed as *send me more of what I like* it is a benefit to the shop, not an extraction — which is the opposite of MKT-4's risk that "a feature that delights owners can repel mechanics". This is the mechanism that resolves that tension.
  - Single source. Worth confirming with an actual shop before building — no working mechanic has been spoken to yet.

- **MKT-4** — *(gated on supply-side adoption — do not build early)* As an Enthusiast, I want to see whether a shop will **fit parts I supply**, so sourcing my own part does not leave me unable to find anyone to install it.
  - Why it is valuable: shops differ on this and it is normally an awkward phone call. Declaring it turns a negotiation into a filter, and it serves the wedge directly — *the least I need to spend to run my car safely*.
  - **Why it is gated:** parts are margin for a shop. A field that publicly commits them to fitting customer-supplied parts undercuts that, and a shop reading the app as pressure may decline to join at all. The feature cannot be tested without shops on the platform, and shipping it early could be what prevents shops joining. That is a **supply-side adoption risk**, not a technical dependency — no amount of engineering removes it.
  - Do not build before there is real shop participation to put at risk. Validate first by asking shops directly whether they would state a policy publicly; if they would not, this becomes a per-quote question rather than a filter, which is a much weaker feature and probably not worth building.
  - Note the asymmetry this reveals generally: in a two-sided marketplace a feature that delights owners can repel mechanics. Worth checking every marketplace story against both sides before building it.

### EPIC: Maintenance Records & Resale
- **MAINT-1** — As an Enthusiast, I want to log a completed maintenance event with **multi-modal evidence** — photos of the work, a video of it being performed, and a screenshot/receipt of the parts order — so each service is documented and verifiable.
- **MAINT-2** — As an Enthusiast, I want the app to **generate a clean maintenance report** per event (and a full service history), so I can *prove upkeep when selling the car* and command a better price — an owner-generated, verifiable service record.
  - **Confirmed 2026-09-06** (`docs/market/findings/2026-09-06-wekfest-chicago.md`, finding 5). Someone who sold three VWs: the dealership "wasn't as bad", but a **private buyer** needed records of parts bought to show service was done — plus "a good vibe". First confirmation of this premise from someone who has actually sold a car.
  - Two refinements it forces. The audience is **private sales specifically** — dealers do not need convincing. And "a good vibe" alongside the receipts means the **report itself is a design constraint**, not just the data behind it: trust in a private sale is part evidence, part presentation.
  - The framing worth keeping: a shop's service history is portable and credible; a DIYer's is a shoebox of receipts. Dealerships and shops have the upper hand today. This levels it.
- **MAINT-3** — As a Dev, I want maintenance evidence auto-linked to the **parts order (MKT-3)** and the **vehicle record (STORE-3)**, so the report ties the work to the actual part and car, not just a loose photo.
- Note: storage — media (photos/video) to object storage (S3/GCS) with metadata in Postgres; keep media costs bounded (compression, retention). A later RAG/agent tie-in could summarize the history or flag gaps.
