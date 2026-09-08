# Feature catalog

What exists in this codebase, what built it, and where to look. One file per feature.

**Read this index first.** Each row names one file below; open only the one you need
rather than reading the whole catalog.

| Feature | ID | Status | What it is |
|---|---|---|---|
| [OBD reader](obd-reader.md) | `OBD` | shipped | Turns raw ELM327 bytes from a car into typed reading records |
| [Fault detection](fault-detection.md) | `DIAG` | shipped | Turns a fault code like `P0217` into meaning, urgency and a location on the car |
| [Decision curator](decision-curator.md) | — | in progress | Drafts the decision log from each session and opens a PR |

## Conventions

Every feature file has the same shape, so you can jump straight to the section you want
without reading the file top to bottom:

| Section | Answers |
|---|---|
| front matter | machine-readable: id, status, stories, PRs, key files |
| **What it does** | one paragraph, no jargon. A concrete input → output example beats any description |
| **How it works** | the runtime path, and the one non-obvious design choice — not a tour of every function, that is what the code is for |
| **History** | every PR that shaped it, one line each |
| **Gotchas** | what surprises people, and what not to "fix". **The most valuable section** — it is the part not recoverable from reading the code |
| **Related** | other features, stories, open issues |

**Starting a new one: copy the closest existing file.** No template is kept in the repo —
it would be a fourth thing to hold in step with three real examples, and it goes stale the
first time the convention shifts. The examples cannot, because they *are* the thing being
described.

Rules that keep this useful rather than another thing that rots:

- **The PR that ships a change writes its own entry**, in the same diff. If the PR
  merged, the entry merged — there is no separate step to forget. This is a step in
  the `/new-pr` skill, not a ritual.
- **Filenames are stable and lowercase-hyphenated.** They get linked to; renaming
  breaks links.
- **Each file stands alone.** A reader should not need to open three files to
  understand one.
- **Plain markdown only** — no HTML, no extensions. Front matter is YAML between `---`
  because that parses everywhere.
- **Use the distinctive words.** `_P04_SUBZONE` is findable; "the zone table" is not.
  This catalog is searched with `grep` far more often than it is read.

## Related

- [`BACKLOG.md`](../../BACKLOG.md) — what is *not* built yet. This catalog is the inverse.
- [`DECISIONS.md`](../../DECISIONS.md) — *why* choices were made. This catalog says *what exists*.
- GitHub Issues — what is queued right now.
- [`testing.md`](testing.md) — the three kinds of test and what each one answers. Moved from the README 2026-09-08.
