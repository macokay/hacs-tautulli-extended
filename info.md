# Tautulli Extended

Extended Plex statistics for Home Assistant via Tautulli.

## What you get

- **Total Movies** — sum of all Plex movie libraries
- **Total TV Shows** — number of shows (not seasons/episodes)
- **Active Streams** — live stream count with per-session details (movie vs. episode, user, progress)
- **Streams (7 Days)** — total plays in the last week
- **Streams (30 Days)** — total plays in the last month

## Requirements

- A running Tautulli instance with API access
- Tautulli API key (found in Tautulli → Settings → Web Interface)
- Home Assistant 2023.1.0 or newer

## Getting started

Install via HACS, restart Home Assistant, then add the integration from **Settings → Devices & Services**. Enter your Tautulli URL and API key — done.
