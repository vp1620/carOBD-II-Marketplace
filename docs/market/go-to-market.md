# Go to market

> **Status: entirely hypothesis.** No customer has been interviewed, no shop approached,
> and the product is not deployed. Nothing below is verified.

## The problem this has to solve

Two chicken-and-egg problems at once:

1. **Hardware.** Someone has to buy an OBD-II dongle before any of this works.
2. **Two sides.** A marketplace needs enthusiasts *and* mechanics, and neither joins for
   an empty platform.

## Current hypothesis: shops give the devices away

A mechanic shop hands customers a dongle as a promotional / retention program.

**Why the shop would do it.** Retention is a thing shops already spend money on. A
$15–30 dongle against one retained service visit is easy payback, and the app keeps them
present between visits — which postcards and oil-change reminders do badly.

**Why it solves the hardware problem.** The customer's barrier drops to zero. They did
not choose to buy a diagnostic device; they were given one by someone they already trust.

**Precedent.** Insurers hand out telematics dongles (Progressive Snapshot and similar),
so the concept will not be alien to either side.

**Second-order benefit.** A shop giving away devices to keep a customer is optimising for
relationship over transaction — which is also the shop most likely to fit
customer-supplied parts (MKT-4). The population most likely to adopt is the population
where that risk is smallest.

### What this changes

`DEVELOPMENT_PLAN.md` currently says the B2C enthusiast leads and the mechanic side is a
second segment. **This inverts that** — the shop becomes the buyer who acquires the
enthusiast. The product barely changes; the first conversation, the pitch and the sales
motion all do.

Not wrong. But you cannot run both first, and this should be a deliberate choice rather
than a drift.

### The question that must be settled before pitching any shop

**Who owns the data when the shop supplied the device?**

ROLE-4 designs access as *a grant from the vehicle owner*. A shop that reasons "I gave
you the dongle, so I see your car" collides with that directly — and that expectation
gets set in the first sales conversation, where it is very hard to walk back.

**The defensible position:** the driver owns the data, always. The shop receives a grant
like anyone else, and the driver can revoke it — including when they change shops. The
shop is buying goodwill and default position, not ownership.

That is a harder sell. It is also the only version compatible with what has been designed,
and the only one that survives a customer switching shops.

### Smaller open questions

- **Whose brand?** Shop-branded implies white-labelling, which is real work. Co-branded,
  with the shop shown as "your mechanic", is far cheaper and probably enough.
- **Does it still work if they leave that shop?** If the device is useless elsewhere, that
  is lock-in customers will resent. Works-everywhere-with-your-shop-as-default is the
  version people keep.
- **How many devices before a shop sees signal?** If a shop hands out 20 and three
  customers engage, is that a win or a failure to them? Their bar, not ours.

## The other channel: the Chicago car scene

Direct-to-enthusiast through meets and events. Slower per person, but it is the segment
whose pain is best understood and where the founder has genuine access.

These are not exclusive — but they need different first products. Shops want retention
and diagnosis; enthusiasts want maintenance provenance and not being overcharged.

## What would falsify all of this

Worth writing down so it can actually be checked:

- Shops say they already have a retention tool and will not add another.
- Shops want the data, and walk when told the driver owns it.
- Drivers do not care what a fault code means — they just want to be told what it costs
  to fix. (In which case DIAG-1/2 is not the wedge; a price estimate is.)
- Nobody has ever lost money selling a car for lack of maintenance records, making
  MAINT-2 a solution to a problem people do not feel.

## Related

- `docs/market/validation-questions.md` — how to test the above with real people
- `BACKLOG.md` — MKT-4 (BYO parts, gated on exactly this adoption risk), HW-1
- `DEVELOPMENT_PLAN.md` — the current, and conflicting, wedge statement
