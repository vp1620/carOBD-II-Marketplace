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
// Every zone `describe()` can return has a matching <symbol> in index.html.
// Kept as an explicit list rather than trusting the string: a zone we have not drawn
// yet renders the "unknown" icon instead of an empty box, so the gap is visible.
const ZONE_ICONS = new Set([
  "engine", "transmission", "exhaust", "emissions",
  "ignition", "chassis", "body", "network",
]);

// Markup for one fault's zone icon. Inherits colour from its parent via currentColor,
// so whatever styles severity also styles the icon — no per-severity icon variants.
function zoneIcon(zone) {
  const id = ZONE_ICONS.has(zone) ? zone : "unknown";
  return `<svg class="zone-icon" aria-hidden="true"><use href="#zone-${id}"/></svg>`;
}

function renderFaults(faults) {
  if (!faults.length) {
    bannerEl.classList.add("hidden");
    return;
  }
  const worst = faults.slice().sort((a, b) => rank(b.severity) - rank(a.severity))[0];
  bannerEl.className = `fault-banner ${worst.severity}`;
  bannerEl.textContent = faults.map((f) => `${f.code} — ${f.description}`).join("   •   ");
}

// Route one incoming reading to the UI. Why: one place that knows how a message maps
// to the DOM, so the socket handlers stay trivial.
function render(msg) {
  if (msg.type === "pid") {
    const el = valueEls[msg.name];
    if (el) el.textContent = `${msg.value} ${msg.unit ?? ""}`.trim();
  } else if (msg.type === "dtc") {
    renderFaults(msg.faults || []);
  }
}

// Connect, and auto-reconnect on drop. Why: a lost socket (server restart, laptop
// sleep) should recover on its own without a manual page reload.
function connect() {
  const ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    statusEl.textContent = "live";
    statusEl.className = "status connected";
  };
  ws.onmessage = (e) => render(JSON.parse(e.data));
  ws.onclose = () => {
    statusEl.textContent = "reconnecting…";
    statusEl.className = "status disconnected";
    setTimeout(connect, 1000); // Why: a simple fixed 1s backoff is plenty for local use.
  };
}

connect();
