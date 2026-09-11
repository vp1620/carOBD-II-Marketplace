# Backlog


Epics and user stories derived from `DEVELOPMENT_PLAN.md`. Phase 1 stories carry
acceptance criteria (they're next); later epics are lighter on purpose — don't
over-specify future work.

**Personas:** **Enthusiast** (budget-conscious car owner, primary) · **Mechanic**
(shop/merchant) · **Dev** (you, for infra/tooling stories).

Story IDs are stable handles for a tracker (Jira/GitHub). Format for seeding an
automated tracker: each `###` epic → an Epic; each `- [ID]` → a Story under it.

---

---

## The phases

| | | Status | Exit criteria |
|---|---|---|---|
| **[Phase 1](phase-1.md)** | a working diagnostic tool | **committed** — specified because it is next | [6 criteria](phase-1.md#exit-criteria--what-done-means), **2 met** as of 2026-09-11 |
| **[Phase 2](phase-2.md)** | the part people actually asked for | **evidenced, not committed** | [4 criteria](phase-2.md#exit-criteria) |
| **[Later](later.md)** | directional | **vision** — deliberately light | none, on purpose |

**Order is priority. Numbering is not.** A story's ID is a stable handle for a tracker; the
order stories appear in is what says which comes first.

## Why phases have exit criteria

Every story here is an **output** — *"I want X so I can Y."* None of them says what
success looks like at the product level. Build all of Phase 1 and have nobody use it, and
the backlog has no way to tell you that.

So each phase carries criteria that are **observable by someone who is not you**, and
deliberately not a feature checklist. Phase 1's criteria 1 and 2 — deployed, and reading a
real car — are still unmet while most of its epics are close to done. That gap is the point:
two of the six criteria were closed by shipping bug fixes (#30, #26), and the two that would
make this a product were untouched by any of it.

## The rule for promotion

An epic leaves [`later.md`](later.md) when there is **evidence** for it. The Marketplace
and Maintenance epics moved to [`phase-2.md`](phase-2.md) because
[Wekfest](../docs/market/findings/2026-09-06-wekfest-chicago.md) produced some. Enthusiasm
is not evidence — including our own.

## Automated tracker seeding

This file is structured so a script/agent can create the tracker in one pass:
epics from `###`, stories from `- [ID]`, acceptance criteria from the `AC:` lines.
Use the story ID as the idempotency key so re-runs update rather than duplicate.
