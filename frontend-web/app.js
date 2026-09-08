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

// Show or clear the fault banner. Why: faults drive the most important UI state, and
// severity picks the color the driver reacts to.
function renderFaults(faults) {
  if (!faults.length) {
    bannerEl.classList.add("hidden");
    return;
  }
  const worst = faults.slice().sort((a, b) => rank(b.severity) - rank(a.severity))[0];
  bannerEl.className = `fault-banner ${worst.severity}`;
  bannerEl.textContent = faults.map((f) => `${f.code} — ${f.description}`).join("   •   ");
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
