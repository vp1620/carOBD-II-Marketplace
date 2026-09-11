// Inner SVG markup for each zone icon, keyed by the zone name describe() returns.
// Why a map here rather than <symbol> elements in index.html: the keys ARE the list of
// zones the frontend can draw, so there is no second list to keep in step. zoneIcon()
// supplies the <svg> wrapper, so the shared viewBox/stroke attributes are written once
// instead of nine times.
// Keys must match backend-OBD-reader/obd_reader/data/dtc_zones.json — a name that does
// not match falls back to "unknown" silently, with no error to notice.
const ZONE_PATHS = {
  // engine: a piston — crown, one compression ring, connecting rod, big end.
  // Redrawn 2026-09-10. It was the check-engine-lamp silhouette, a wide outline with a
  // dozen 2-3 unit steps; at 1.15em each step is under a pixel, so they collapsed into a
  // rounded blob that read like the transmission gear beside it. A piston is vertical,
  // asymmetric and made of four large parts, which is what survives downscaling.
  "engine": '<rect x="7.4" y="3.2" width="9.2" height="7.6" rx="1.2"/><path d="M7.4 7.4h9.2"/><path d="M12 10.8v5.2"/><circle cx="12" cy="18.6" r="2.6"/>',
  "transmission": '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v2.6M12 18.9v2.6M21.5 12h-2.6M5.1 12H2.5M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8M18.7 18.7l-1.8-1.8M7.1 7.1 5.3 5.3"/>',
  // exhaust: a muffler — tip, body with its seam, and the bent outlet pipe.
  // Redrawn 2026-09-10 from a reference. It was a tailpipe with gas wisps, which competed
  // with the emissions cloud for "vapour"; a muffler is a solid object and reads as one.
  "exhaust": '<rect x="5.6" y="8.4" width="11" height="7.2" rx="1.8"/><rect x="2" y="10.2" width="3.6" height="3.6" rx="1.2"/><path d="M8.2 13.6h5.8"/><path d="M16.6 11.2h1.9l2.5-3"/>',
  // emissions: the cloud alone. The two wisps beneath it were removed 2026-09-10 —
  // at 1.15em each was sub-pixel, so they contributed noise rather than meaning.
  "emissions": '<path d="M7 18h9a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 7 11.4 3.3 3.3 0 0 0 7 18z"/>',
  "ignition": '<path d="M13 2 5 13.5h5.5L10 22l8-11.5h-5.5z"/>',
  // chassis: the drivetrain seen from above — four wheels, two axles, a driveshaft.
  // Redrawn 2026-09-10 from a reference. The "H-spine-H" gestalt is unlike anything else
  // in the set, which is what makes it findable at 1.15em; a previous ladder frame read
  // as a grid, and before that a wheel-and-strut read as the piston.
  "chassis": '<rect x="2.4" y="3.2" width="3.6" height="5" rx="1.3"/><rect x="18" y="3.2" width="3.6" height="5" rx="1.3"/><rect x="2.4" y="15.8" width="3.6" height="5" rx="1.3"/><rect x="18" y="15.8" width="3.6" height="5" rx="1.3"/><path d="M6 5.7h12M6 18.3h12"/><path d="M12 5.7v12.6"/>',
  // body: side profile with wheel ARCHES rather than wheels. Redrawn 2026-09-10.
  // The arches matter: chassis now draws wheels as four corner blocks, so filled wheels
  // here would put two circles under a horizontal shape in both icons. Cut-outs read as
  // bodywork, which is also closer to what Bxxxx covers.
  "body": '<path d="M3 17v-4l4-1 3-5h8l2.5 6v4z"/><path d="M6.2 17a2.7 2.7 0 0 1 5.4 0"/><path d="M13.6 17a2.7 2.7 0 0 1 5.4 0"/><path d="M10.8 8.4h5l1.2 3.4h-6.2z"/>',
  "network": '<circle cx="12" cy="4.5" r="2.2"/><circle cx="4.8" cy="19" r="2.2"/><circle cx="19.2" cy="19" r="2.2"/><path d="M12 6.7 5.6 16.9M12 6.7l6.4 10.2M7 19h10"/>',
  "unknown": '<circle cx="12" cy="12" r="9"/><path d="M9.4 9.3a2.7 2.7 0 0 1 5.2.9c0 1.8-2.6 2.2-2.6 4"/><path d="M12 17.6h.01"/>'
};
