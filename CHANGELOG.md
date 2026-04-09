# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.1] - 2026-04-09

### Changed
- Brand icon replaced: PNG removed, SVG added (`brand/icon.svg`)
- README restructured to standard template format — logo, badges, Buy Me A Coffee, structured sections
- Issue templates updated to standard format — added Actual behaviour section and log filter instructions
- `.gitignore` updated with standard exclusions

---

## [1.1.0] - 2026-03-10

### Added
- Active Stream Type sensor — shows Movie, TV Show, Mixed, or Idle
- Streams (1 Year) sensor — total plays in the last 365 days
- Streams (This Year) sensor — total plays since January 1st
- Brand icon for integration UI

### Changed
- Active Streams sensor now focused on count; type info moved to dedicated sensor
- API call optimized: single 365-day request covers all time ranges

---

## [1.0.0] - 2026-03-10

### Added
- Initial release
- Total Movies sensor (auto-sums all movie libraries)
- Total TV Shows sensor (show count, not seasons/episodes)
- Active Streams sensor with per-stream attributes (user, title, media type, player, state, progress)
- Streams (7 Days) sensor with daily breakdown
- Streams (30 Days) sensor with daily breakdown
- Config flow with Tautulli URL + API key validation
- Danish and English translations
- 60-second update interval
