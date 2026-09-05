// Inner SVG markup for each zone icon, keyed by the zone name describe() returns.
// Why a map here rather than <symbol> elements in index.html: the keys ARE the list of
// zones the frontend can draw, so there is no second list to keep in step. zoneIcon()
// supplies the <svg> wrapper, so the shared viewBox/stroke attributes are written once
// instead of nine times.
// Keys must match backend-OBD-reader/obd_reader/data/dtc_zones.json — a name that does
// not match falls back to "unknown" silently, with no error to notice.
const ZONE_PATHS = {
  "engine": '<path d="M3 13v-3h2V8h4v2h3l3-3h2v3h2a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-2v3h-2l-3-3H9v2H5v-2H3z"/><path d="M7 6h4"/>',
  "transmission": '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v2.6M12 18.9v2.6M21.5 12h-2.6M5.1 12H2.5M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8M18.7 18.7l-1.8-1.8M7.1 7.1 5.3 5.3"/>',
  "exhaust": '<path d="M2 15h9a3 3 0 0 1 3 3v1H2z"/><path d="M14 16h5a2 2 0 0 0 0-4h-3"/><path d="M17 8.5c1.4 0 1.4-2 2.8-2M19.5 5c1.4 0 1.4-2 2.8-2"/>',
  "emissions": '<path d="M7 18h9a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 7 11.4 3.3 3.3 0 0 0 7 18z"/><path d="M9 21.5c1.2 0 1.2-1.5 2.4-1.5M14 21.5c1.2 0 1.2-1.5 2.4-1.5"/>',
  "ignition": '<path d="M13 2 5 13.5h5.5L10 22l8-11.5h-5.5z"/>',
  "chassis": '<circle cx="12" cy="16.5" r="4.5"/><circle cx="12" cy="16.5" r="1.3"/><path d="M12 12V7M9.5 7h5M10 4.5h4"/>',
  "body": '<path d="M3 15v-2.2l1.8-4A2 2 0 0 1 6.7 7.5h10.6a2 2 0 0 1 1.9 1.3l1.8 4V15z"/><path d="M4.8 12.8h14.4"/><circle cx="7.5" cy="15.5" r="1.6"/><circle cx="16.5" cy="15.5" r="1.6"/>',
  "network": '<circle cx="12" cy="4.5" r="2.2"/><circle cx="4.8" cy="19" r="2.2"/><circle cx="19.2" cy="19" r="2.2"/><path d="M12 6.7 5.6 16.9M12 6.7l6.4 10.2M7 19h10"/>',
  "unknown": '<circle cx="12" cy="12" r="9"/><path d="M9.4 9.3a2.7 2.7 0 0 1 5.2.9c0 1.8-2.6 2.2-2.6 4"/><path d="M12 17.6h.01"/>'
};
