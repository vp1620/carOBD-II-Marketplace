# Learning stories

Problem statements for work Vishvesh implements himself. One file per story.

## The rule

- **Claude writes the problem and a resource list.** No code, no solution, no worked example.
- **AI is for finding resources** — docs, references, "where is this documented" — not for
  producing the answer.
- **You implement**, then we compare your reading of problem → resources → solution against
  mine. My opinions stay unstated until yours are written down; otherwise it is just me
  writing the code slowly.
- **Claude may be wrong.** Saying so is the point, not a side effect.

## Why these are real work, not exercises

Every one solves something the project actually needs. A tutorial you throw away teaches
less than the same hours spent on a problem with consequences — and the questions in each
file are the ones you would be asked in a review, so answering them is practice for that too.

## Stories

| | Topic | Solves | Status |
|---|---|---|---|
| **LEARN-1** | `POST /scan` — REST design, and a lock vs a rate limiter | on-demand DTC read; Track 2 | not started |
| **[LEARN-2](LEARN-2-dockerfile.md)** | Containerise the backend | #13, and Phase 1 exit criterion 1 | not started |

## Answering

Put the answers in the **PR description**, not in this folder. They are the review — a
working implementation with no reasoning is worth less here than a broken one with good
reasoning, because the reasoning is the part that transfers.
