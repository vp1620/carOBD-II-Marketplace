// Live dashboard client: connect to the backend WebSocket and render readings.
// Why vanilla JS: Phase 1 wants a working page with zero build toolchain.

// Same-origin WS URL. Why: FastAPI serves both this page and the feed, so we derive
// the socket address from the page location instead of hardcoding a host.
const WS_URL = `ws://${location.host}/ws`;

// Cache each card's value element by sensor name once. Why: avoid re-querying the DOM
// on every incoming message, which can arrive many times per second.
const valueEls = {};
document.querySelectorAll(".card").forEach((card) => {
  valueEls[card.dataset.name] = card.querySelector(".value");
});

const statusEl = document.getElementById("status");
const bannerEl = document.getElementById("fault-banner");

// Map a severity to a sort rank. Why: lets the banner reflect the worst active fault
// when several are present at once.
function rank(sev) {
  return { info: 0, warning: 1, critical: 2 }[sev] ?? 0;
}

// Seconds each fault is shown before the banner moves to the next one.
const FAULT_CYCLE_MS = 1500;

// Active faults, and which one is currently on screen. Why this is module state rather
// than a local: the server re-sends the same fault list every few seconds, and the
// display has to survive that. Rebuilding from each message is what made the banner
// restart at the first code and never reach the others.
let faults = [];
let faultIndex = 0;
let faultTimer = null;

// Are these the same faults we are already showing?
//
// Compared as a SORTED set of codes, deliberately. `faults` is stored worst-severity
// first while the server sends them in whatever order the ECU reported, so comparing
// position-by-position never matched — every DTC read looked like a new set and reset the
// cycle to the first code. With a 3s cycle and a 5s DTC read that showed 1/8, 2/8, then
// jumped back to 1/8 forever.
//
// Order is not part of the identity here: the same eight codes are the same eight faults
// however they arrive.
function sameFaults(next) {
  if (next.length !== faults.length) return false;
  const a = next.map((f) => f.code).sort();
  const b = faults.map((f) => f.code).sort();
  return a.every((code, i) => code === b[i]);
}

// Draw whichever fault is currently up. One at a time, deliberately: eight codes joined
// with bullets is a wall of text nobody reads, and the severity colour is meaningless
// when it has to represent eight different severities at once. Showing one lets the
// banner's colour be that fault's colour.
function showCurrentFault() {
  const f = faults[faultIndex];
  if (!f) return;
  bannerEl.className = `fault-banner ${f.severity}`;
  const position = faults.length > 1 ? `  (${faultIndex + 1}/${faults.length})` : "";
  // innerHTML, not textContent, because zoneIcon() returns markup — textContent would
  // print the <svg> tags as visible characters. Safe today: f.code and f.description come
  // from our own dtc_generic.json. It stops being safe at DIAG-3, where descriptions can
  // come from a community source; that is when this should build nodes instead.
  bannerEl.innerHTML = `${zoneIcon(f.zone)} ${f.code} — ${f.description}${position}`;
}

// Markup for one fault's zone icon. Inherits colour from its parent via currentColor,
// so whatever styles severity also styles the icon — no per-severity icon variants.
function zoneIcon(zone) {
  const paths = ZONE_PATHS[zone] || ZONE_PATHS.unknown;
  return `<svg class="zone-icon" aria-hidden="true" 
               viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
               stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
}
// Show or clear the fault banner. Why: faults drive the most important UI state, and
// severity picks the color the driver reacts to.
//
// Empty means the ECU reported no active faults, which is a real answer and not a gap —
// so the banner genuinely does hide. It should not hide *between* two reads that both
// had faults; that was a bug where the fixture emitted faults from two places and one of
// them sent an empty set once per cycle.
function renderFaults(next) {
  if (!next.length) {
    faults = [];
    clearInterval(faultTimer);
    faultTimer = null;
    bannerEl.classList.add("hidden");
    return;
  }

  // An unchanged list must not restart the cycle. The server re-sends the same faults on
  // every DTC read, so resetting here would pin the banner to the first code forever.
  if (sameFaults(next)) return;

  // Worst first, so the most urgent fault is the one on screen when the banner appears.
  faults = next.slice().sort((a, b) => rank(b.severity) - rank(a.severity));
  faultIndex = 0;
  bannerEl.classList.remove("hidden");
  showCurrentFault();

  clearInterval(faultTimer);
  faultTimer = faults.length > 1
    ? setInterval(() => {
        faultIndex = (faultIndex + 1) % faults.length;
        showCurrentFault();
      }, FAULT_CYCLE_MS)
    : null;
}

// How each backend source is shown. Why a table rather than branching in render():
// adding a source later is a row here, and the label/class pair stays in one place so a
// new state cannot get a colour without getting a label.
//
// The distinction this exists for: the pill used to be set inside ws.onopen, so it
// reported that the WEBSOCKET connected — nothing about whether a car was attached. It
// said "live" over recorded data, and would have said "live" with no adapter at all.
const SOURCES = {
  live:         { label: "live",              cls: "connected" },
  replaying:    { label: "replaying recording", cls: "replaying" },
  disconnected: { label: "no adapter",        cls: "disconnected" },
};

// Show what the browser is actually looking at. Why the detail goes in `title` and not on
// screen: "ConnectionError: could not open /dev/cu.usbserial" helps whoever is debugging
// and means nothing to a driver, so it is available on hover without occupying the pill.
function renderStatus(msg) {
  const s = SOURCES[msg.source] || SOURCES.disconnected;
  statusEl.textContent = s.label;
  statusEl.className = `status ${s.cls}`;
  statusEl.title = msg.detail || "";
}

// Route one incoming reading to the UI. Why: one place that knows how a message maps
// to the DOM, so the socket handlers stay trivial.
function render(msg) {
  if (msg.type === "pid") {
    const el = valueEls[msg.name];
    if (el) el.textContent = `${msg.value} ${msg.unit ?? ""}`.trim();
  } else if (msg.type === "dtc") {
    renderFaults(msg.faults || []);
  } else if (msg.type === "status") {
    renderStatus(msg);
  }
}

// Connect, and auto-reconnect on drop. Why: a lost socket (server restart, laptop
// sleep) should recover on its own without a manual page reload.
function connect() {
  const ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    // Deliberately does NOT say "live". Opening the socket proves the server is up, not
    // that a car is attached — conflating the two is the whole of #26. The server sends a
    // status message on connect; until it arrives we say only what we know.
    statusEl.textContent = "connecting…";
    statusEl.className = "status connecting";
  };
  ws.onmessage = (e) => render(JSON.parse(e.data));
  ws.onclose = () => {
    // The SERVER is unreachable — a different failure from the adapter being unplugged,
    // and worth distinguishing, since one is our fault and the other is the driver's cable.
    statusEl.textContent = "no server";
    statusEl.className = "status disconnected";
    statusEl.title = "";
    setTimeout(connect, 1000); // Why: a simple fixed 1s backoff is plenty for local use.
  };
}

connect();
