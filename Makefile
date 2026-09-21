# Shortcuts for running the dashboard against a recorded scenario.
#
# WHY THIS EXISTS
#   Switching scenarios means setting OBD_FIXTURE to a path under simulated_codes/ and
#   remembering the venv's python. That is two things to remember and one of them is easy
#   to get subtly wrong (a system python starts, then fails on `import uvicorn`). `make
#   run-limp-mode` is one thing to remember, and the scenario names tab-complete.
#
#   This is a thin wrapper, not a layer: every target below is one `OBD_FIXTURE=... python
#   main.py` line. Nothing here knows anything the app does not already know, so it cannot
#   drift away from how the app actually behaves.
#
# SCOPE
#   Same expiry as simulated_codes/ itself — when real captured traces replace the
#   hand-written scenarios (see obd_reader/scenario.py), the run-* targets go with them.

# Overridable so this works if the venv is ever named something else, or under CI where
# python is already on PATH: `make run PY=python3`.
PY  ?= ./obdvenv/bin/python
APP := backend-OBD-reader/main.py

# Scenario names derived from the directory rather than listed here, so adding a file to
# simulated_codes/ gives you a working target with no edit to this file.
#
# catalog-additions is excluded because it is not a scenario — it is a review queue of
# proposed DTC catalog entries with no `records` key, so replaying it would fail with a
# KeyError rather than tell you anything.
NOT_SCENARIOS := catalog-additions
SCENARIOS := $(filter-out $(NOT_SCENARIOS),$(basename $(notdir $(wildcard simulated_codes/*.json))))

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo 'Run the dashboard on http://localhost:8000'
	@echo ''
	@echo '  make run                 day rotation (changes overnight, same all day)'
	@echo '  make run-<scenario>      one specific recording'
	@echo '  make live PORT=/dev/...  a real ELM327 adapter'
	@echo '  make scenarios           what each recording contains'
	@echo ''
	@echo 'Scenarios: $(SCENARIOS)'

.PHONY: scenarios
scenarios:
	@echo 'gas-cap            P0442 — one benign fault'
	@echo 'severity-mix       P0171, P0217, P0442 — three severity levels at once'
	@echo 'all-zones          eight codes, one per zone — every icon on screen'
	@echo 'uncatalogued       codes with no catalog entry — fallback rendering'
	@echo 'limp-mode          12 codes — worst case, dense banner'
	@echo 'healthy            no faults (deliberately outside the rotation)'
	@echo ''
	@echo 'The first five rotate by calendar day. Each run prints which it chose.'

# The default run: no OBD_FIXTURE set, so reader.py falls through to the day rotation.
.PHONY: run
run:
	$(PY) $(APP)

# One target per scenario, via a pattern rule. The guard turns `make run-typo` into a
# readable error instead of make's "No rule to make target", which sends you reading this
# file to find out what you typed wrong.
#
# It checks membership in SCENARIOS rather than `test -f` on the path: the excluded file
# exists, so a file check would happily launch the server on catalog-additions and leave
# you staring at an empty dashboard wondering what broke.
#
# Deliberately NOT .PHONY: make skips implicit-rule search for phony targets, so declaring
# the run-* names phony stops this pattern from matching them at all — every scenario then
# reports "Nothing to be done" and exits 0, which looks like success. No file named run-*
# exists, so the rule fires every time regardless.
run-%:
	@test -n "$(filter $*,$(SCENARIOS))" || { \
		echo "no scenario named '$*'"; \
		echo "available: $(SCENARIOS)"; \
		test -f simulated_codes/$*.json && \
			echo "(simulated_codes/$*.json exists but is not a replayable recording)"; \
		exit 1; \
	}
	OBD_FIXTURE=simulated_codes/$*.json $(PY) $(APP)

# PORT rather than OBD_PORT so the command line stays short; it is exported under the name
# reader.py actually reads. Checked up front because a missing value silently falls back to
# a fixture, and "why is my car not showing up" is a bad way to discover a typo.
.PHONY: live
live:
	@test -n "$(PORT)" || { \
		echo 'set PORT to the adapter device, e.g.'; \
		echo '  make live PORT=/dev/tty.usbserial-1410'; \
		echo 'candidates:'; \
		ls /dev/tty.* 2>/dev/null | sed 's/^/  /' || echo '  (none found)'; \
		exit 1; \
	}
	OBD_PORT=$(PORT) $(PY) $(APP)
