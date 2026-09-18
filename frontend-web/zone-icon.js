// Inner SVG for each zone icon. zoneIcon() in app.js wraps these in an <svg>.
// Keys must match backend-OBD-reader/obd_reader/data/dtc_zones.json.
// To see them rendered: python backend-OBD-reader/tools/show_icons.py
// Why each is the shape it is, and the 18px rule they follow: that script's docstring.

const ZONE_PATHS = {
  "engine": '<rect x="7.4" y="3.2" width="9.2" height="7.6" rx="1.2"/><path d="M7.4 7.4h9.2"/><path d="M12 10.8v5.2"/><circle cx="12" cy="18.6" r="2.6"/>',
  "transmission": '<circle cx="9" cy="9.4" r="5.4"/><circle cx="9" cy="9.4" r="1.9"/><circle cx="17.4" cy="16.2" r="3.6"/><circle cx="17.4" cy="16.2" r="1.3"/>',
  "exhaust": '<rect x="5.6" y="8.4" width="11" height="7.2" rx="1.8"/><rect x="2" y="10.2" width="3.6" height="3.6" rx="1.2"/><path d="M8.2 13.6h5.8"/><path d="M16.6 11.2h1.9l2.5-3"/>',
  "emissions": '<path d="M7 18h9a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 7 11.4 3.3 3.3 0 0 0 7 18z"/>',
  "ignition": '<path d="M13 2 5 13.5h5.5L10 22l8-11.5h-5.5z"/>',
  "chassis": '<rect x="2.4" y="3.2" width="3.6" height="5" rx="1.3"/><rect x="18" y="3.2" width="3.6" height="5" rx="1.3"/><rect x="2.4" y="15.8" width="3.6" height="5" rx="1.3"/><rect x="18" y="15.8" width="3.6" height="5" rx="1.3"/><path d="M6 5.7h12M6 18.3h12"/><path d="M12 5.7v12.6"/>',
  "body": '<path d="M3 17v-4l4-1 3-5h8l2.5 6v4z"/><path d="M6.2 17a2.7 2.7 0 0 1 5.4 0"/><path d="M13.6 17a2.7 2.7 0 0 1 5.4 0"/><path d="M10.8 8.4h5l1.2 3.4h-6.2z"/>',
  "network": '<circle cx="12" cy="4.5" r="2.2"/><circle cx="4.8" cy="19" r="2.2"/><circle cx="19.2" cy="19" r="2.2"/><path d="M12 6.7 5.6 16.9M12 6.7l6.4 10.2M7 19h10"/>',
  "unknown": '<circle cx="12" cy="12" r="9"/><path d="M9.4 9.3a2.7 2.7 0 0 1 5.2.9c0 1.8-2.6 2.2-2.6 4"/><path d="M12 17.6h.01"/>',
};
