# LEARN-2 — containerise the backend

> **Learning-opportunity format.** This file is a problem statement and a resource list.
> There is no solution in it, and no Dockerfile. You write the code; AI is for *finding
> resources* — docs, references, "where is this documented" — not for producing the answer.
> Afterwards we compare your reading of problem → resources → solution against mine.
>
> Claude may be wrong about something in here. Say so when you think it is; that is the point.

---

## The problem

Package the backend so it runs on a machine with **no Python installed, no venv, and no
knowledge of this repo's layout**.

Success is one command producing a working dashboard on a machine that has only Docker.

This is not busywork. It is the shortest path to **Phase 1 exit criterion 1** — *"a stranger
can use it without you present"* — which is currently unmet, and it is the same work as
**#13**, seen from a different angle: a `Dockerfile` is an *executable* dependency
declaration. It cannot drift, because if it is wrong the build fails.

---

## Questions to answer

Tick these off as you go. Answer them in the PR description when you open it — they are the
review, not a formality. A working Dockerfile with no reasoning is worth less here than a
broken one with good reasoning, because the reasoning is the part that transfers.

- [ ] **Q1** — base image, and why "smallest" is not automatically right
- [ ] **Q2** — what is copied, in what order, and what that ordering exploits
- [ ] **Q3** — the three runtime paths *(the one worth the time)*
- [ ] **Q4** — what must never enter the image, and how you verified it did not
- [ ] **Q5** — the 2GB dependency problem
- [ ] **Q6** — what the container does with no car attached

### Q1 — Which base image, and why?

- [ ] answered in the PR description

`python:3.14`, `python:3.14-slim`, and `python:3.14-alpine` differ by roughly an order of
magnitude in size.

Alpine has a specific, well-documented problem with Python packages shipping compiled
wheels. **Find out what that problem is and why it happens** before choosing — the answer
involves a C library, and it is the reason "smallest image" is not automatically the right
call.

*Answer with:* the variant you picked, the resulting image size, and the tradeoff you
accepted.

### Q2 — What is copied, and in what order?

- [ ] answered in the PR description

Docker caches each instruction as a layer and reuses the cache until something changes.

There is a conventional ordering for Python images that makes a source-code change *not*
reinstall every dependency. **Work out what that ordering exploits.**

*Answer with:* your ordering, and roughly how long a rebuild takes after changing one line
in `server.py` versus after changing `requirements.txt`. The gap is the point.

### Q3 — the interesting one: three paths computed at runtime

- [ ] answered in the PR description

```
reader.py:20    _REPO_ROOT    = dirname(__file__)/../..
server.py:166   _FRONTEND_DIR = dirname(__file__)/../../frontend-web
reader.py:21    _FIXTURE      = _REPO_ROOT/test_files/sample_obd_output.json
```

Every one walks **up two directories** from a module inside `backend-OBD-reader/obd_reader/`.
So the container has to preserve the *relative* layout of:

```
backend-OBD-reader/    frontend-web/    test_files/    simulated_codes/
```

Copy only the backend and you get a server that starts perfectly and 404s the dashboard.

**Two ways to solve it:**

- **Reproduce the layout in the image** — a Docker problem, solved in the Dockerfile
- **Change the code so paths do not depend on repo layout** — a design problem, solved in Python

*Answer with:* which you chose and why. Be ready to defend it — this is the question with a
real argument on both sides, and it is the one I most want to hear your reasoning on before
I give mine.

### Q4 — What must never be copied into the image?

- [ ] answered in the PR description

`obdvenv/` is **59MB** and will be copied unless you stop it. There is a specific file that
prevents this. Find out what it is called, and what *else* belongs in it for this repo.

*Answer with:* the file, its contents, and how you verified the venv is genuinely not in
the image. "It looks smaller" is not verification — find the command that lists what is
actually inside.

### Q5 — The dependency problem you will hit immediately

- [ ] answered in the PR description

```
requirements.txt:   sentence-transformers>=2.6   # pulls in torch — heavy
                    qdrant-client>=1.9
```

Your image will be roughly **2GB to run a serial reader**. Neither package is imported by
anything under `obd_reader/`.

This is **#13**. You have three options: fix #13 first, work around it in the Dockerfile, or
ship a 2GB image and open an issue.

*Answer with:* which you chose. All three are defensible; shipping 2GB silently is not.

### Q6 — What does this container actually do without a car?

- [ ] answered in the PR description

There is no adapter attached to a deployed container, and on macOS there cannot be — Docker
runs in a VM and USB passthrough is not practical.

**On your Linux machine it is different**: `--device=/dev/ttyUSB0` works. Note the device is
`/dev/ttyUSB0` or `/dev/ttyACM0`, **not** `/dev/cu.*`, and your user must be in the
`dialout` group or the open fails with a permission error that reads like the device is
missing.

*Answer with:* what the container does by default with no `OBD_PORT` set, and whether you
think the deployed version should ever be the hardware one.

---

## Things you do not have to worry about

`main.py` already binds `0.0.0.0`, so the server is reachable from outside the container.
You do still need to know **why that matters** and what you do at `docker run` to reach it —
binding correctly and publishing the port are two different things.

---

## Resources

Deliberately not links to a finished Dockerfile.

**Official, and enough on their own**
- Docker — *Containerize a Python application* (the official language-specific guide)
- Docker — **Dockerfile reference**. Read `FROM`, `WORKDIR`, `COPY`, `RUN`, `EXPOSE`, `CMD`,
  and specifically **how `CMD` differs from `ENTRYPOINT`**
- Docker — **`.dockerignore`** documentation
- Docker Hub — **Python Official Image** page, for the variant comparison in Q1
- Docker — *Best practices for writing Dockerfiles*, particularly the layer-caching section

**Commands you will need**
```
docker build -t carobd .
docker run -p 8000:8000 carobd
docker run -e OBD_FIXTURE=... carobd
docker run --device=/dev/ttyUSB0 ...        # Linux only
docker images                                # image size
docker run --rm -it carobd sh                # look inside
```

**For Q1 specifically:** search for why Alpine and Python wheels interact badly. The term
you are looking for involves the C standard library, and once you have it the tradeoff is
obvious.

---

## How you know it worked

```bash
docker build -t carobd .
docker run -p 8000:8000 carobd
```

Ordered so a partial pass tells you *which* thing is wrong:

- [ ] **`localhost:8000` loads the dashboard** — page, CSS, gauges
- [ ] **The zone icons render.** The real check on Q3: icons come from
      `frontend-web/zone-icon.js`, served through `_FRONTEND_DIR`. Broken layout, no icons
- [ ] **`-e OBD_FIXTURE=simulated_codes/limp-mode.json` changes what you see** — twelve
      faults instead of today's rotation. Proves `_REPO_ROOT` resolves too, which is a
      *different* path from the frontend one
- [ ] **`docker images` shows a size you can justify** in Q1 and Q5
- [ ] *(Linux only)* **`--device=/dev/ttyUSB0` reaches a real adapter** — optional, and
      gated on the vLinker arriving

If the first two tick but the third does not, you solved half of Q3 — the frontend path
resolves and the fixture path does not. Worth understanding why before fixing it.

---

## When you are done

Open the PR with the six answers in the description. Then we compare readings — I have
opinions on **Q1, Q3 and Q5** and I will hold them until yours are written down, because
otherwise this is just me writing a Dockerfile slowly.

**Related:** #13 (dependency drift) · `backlog/phase-1.md` exit criteria 1 and 6 ·
LEARNING.md item 15 (CI/CD) — a container is what CI would build and what a deploy target
would run.
