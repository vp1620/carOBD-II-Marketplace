# Validation question bank

For talking to real people at events. First outing: **Wakefest, Sat 2026-09-06.**

---

## Read this first — it decides whether the day is worth anything

**Do not describe the product until the end.** The moment you pitch, people start being
polite, and polite answers are worthless. Ask about their life; mention what you are
building only when they ask or as you leave.

**Ask about the past, never the future.** "Would you use this?" reliably gets a yes that
means nothing. "What did you do last time?" gets a fact.

| Useless | Useful |
|---|---|
| "Would you pay for this?" | "What did that repair end up costing you?" |
| "Would an app like this help?" | "Walk me through the last time your check engine light came on." |
| "Do you care about maintenance records?" | "When you sold your last car, what did the buyer ask for?" |
| "Is that annoying?" | "What did you do about it?" |

**Signals that mean something:** money already spent, time already wasted, a workaround
they built themselves, an emotional reaction, or them asking *you* a follow-up question.

**Signals that mean nothing:** "cool idea", "I'd definitely use that", "you should add…"
delivered with no story behind it.

**Write it down within five minutes.** Not later. You will lose the specifics, and the
specifics are the whole point.

## A note on the segments

They are split by **relationship to the car and to repair shops**, not by knowledge.
The reason there is a separate set for women is a documented one: research on automotive
service repeatedly finds women are quoted higher prices and report being talked down to.
That is a real pain a transparency product could address — and it is the thing worth
asking about. Do not ask questions that presume how much anyone knows; several people
will know far more than expected.

**Wakefest is a Subaru event.** Expect it to be overwhelmingly enthusiast. The two
"average owner" sets will be thin on the ground — likely partners, friends and family who
came along. Adapt rather than forcing the script.

---

## Everyone — open with these

1. What are you driving, and how long have you had it?
2. What is the last thing that went wrong with it?
3. What did you do about it — who did you call, what did it cost, how long did it take?
4. Where do you get it serviced? How did you pick them?

*Everything below hangs off the answers to these. If you only get four questions in,
these are the four.*

---

## Enthusiast

The core segment. They already diagnose by ear, own tools, and have opinions about shops.

⭐ **1. Tell me about the last time you diagnosed something yourself. How did you work
out what it was?**
⭐ **2. Last time you sold a car — what did the buyer ask about how you'd looked after it?
Were you able to show them anything?** *(tests **MAINT-2**, the strongest story)*
⭐ **3. Do you have an OBD reader? Which one, what do you use it for, and when did you
last plug it in?** *(tests whether the hardware barrier is even real for this group)*

4. Have you ever had a code you couldn't work out what it meant? What did you do?
5. When you buy parts, where from, and how do you decide? *(MKT-1)*
6. Has a shop ever refused to fit a part you supplied? *(MKT-4 — the gated one)*
7. Is there a noise your car makes that you have never got to the bottom of? *(PRED-8)*
8. Who else drives or works on your car? Do you ever need to show them what it's doing?
   *(ROLE-4)*
9. If a shop handed you a free plug-in device that shared data with them, would you use
   it — and would you want to be able to turn that off? *(the go-to-market hypothesis,
   and the data-ownership question)*

---

## Average owner — male

Drives it, doesn't work on it. The car is transport, not a hobby.

⭐ **1. Last time your check engine light came on — what went through your head, and
what did you actually do?**
⭐ **2. Have you ever felt you were charged for something you didn't need? What
happened?**

3. Do you know what's due on your car right now? How would you find out?
4. Where do you take it, and how did you end up there?
5. When they tell you what's wrong, do you understand the explanation? Do you check it
   anywhere?
6. Have you ever put off a repair because you weren't sure it was urgent? *(tests
   `deferrable` — **DIAG-2**)*
7. What did you do about maintenance records when you last sold a car? *(MAINT-2)*
8. If your mechanic gave you a device that let them see the car between visits, how would
   you feel about that? *(the giveaway program, honestly asked)*

---

## Average owner — female

Same relationship to the car. The extra questions probe treatment at shops, which is the
documented differential and the thing a transparency tool could change.

⭐ **1. Last time you took the car in — how did that go? Did you feel like you got a
straight answer?**
⭐ **2. Have you ever taken someone with you to a garage, or had someone else make the
call for you? Why?**

3. Last time the check engine light came on, what did you do?
4. Do you feel like you can tell whether a quote is fair? What do you do to check?
5. Have you ever been quoted something that turned out to be unnecessary, or been talked
   down to? What happened after?
6. Would it change anything to walk in already knowing what the code meant and roughly
   what it should cost? *(the transparency value proposition — note this one is
   hypothetical, so weight the answer lightly)*
7. Who do you ask when you're not sure about something with the car? *(ROLE-4 sharing
   — the "ask a knowledgeable friend" pattern)*
8. What did you do about maintenance records when you last sold a car? *(MAINT-2)*

---

## Mechanic / shop

The supply side, and where the go-to-market lives or dies.

⭐ **1. How do customers usually describe a problem when they call? How often are they
right?**
⭐ **2. What do you do today to keep customers coming back? Does any of it work?**
   *(the whole giveaway premise rests on this answer)*
⭐ **3. If a customer walked in with a printout of the fault codes and their recent data,
would that help you or get in the way?** *(this can go either way and the honest answer
matters)*

4. How often do you get a comeback — the same car back for the same problem?
5. Do you fit parts customers bring in? Why / why not? *(MKT-4 — ask it neutrally, do
   not sell)*
6. Would you hand a customer a free plug-in device if it kept them connected to you?
   What would it need to do for that to be worth it? *(the core GTM question)*
7. If you gave them the device, whose data would you consider it? *(the question to
   settle before pitching anyone — listen carefully here)*
8. What software are you already running? What do you hate about it?
9. How many cars a week, and what's the mix — do you specialise?

---

## Feature suggestions — ask at the end, once

Once, near the end of a conversation, after they've told you about their actual life:

> **"If you could change one thing about owning / working on this car, what would it be?"**

Then shut up. The answer is more valuable than anything in the sections above, and it is
the only question here designed to surface things not already in `BACKLOG.md`.

If they offer a feature idea, ask the follow-up that separates real from polite:

> **"When did you last need that?"**

---

## Recording

One line per person, in `findings/2026-09-06-wakefest.md`:

```
[segment] car, how long | the problem they described | what they DID | £/$ and time
| anything they asked me | quotes worth keeping verbatim
```

Verbatim quotes are worth more than your summary. Write the words they used.

## Afterwards

Update `go-to-market.md` — specifically the **"What would falsify all of this"** section.
Any assumption that survived contact gets marked verified with a date; any that did not
gets rewritten. That is the entire point of going.
