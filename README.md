# Tautulli Extended — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/macokay/hacs-tautulli-extended.svg)](https://github.com/macokay/hacs-tautulli-extended/releases)
[![License](https://img.shields.io/badge/license-Non--Commercial-blue.svg)](#license)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1.0+-brightgreen.svg)](https://www.home-assistant.io/)

An extended Tautulli integration for Home Assistant that exposes detailed Plex media server statistics as sensors — total movies, total TV shows, active streams with media type info, and play counts over 7 and 30 days.

---

## Features

- **Total movies** across all Plex movie libraries (auto-summed)
- **Total TV shows** across all Plex show libraries (show count, not seasons/episodes)
- **Active streams** with per-stream details (user, title, movie vs. episode, player, progress)
- **Streams last 7 days** with daily breakdown
- **Streams last 30 days** with daily breakdown
- GUI config flow — no YAML needed
- Danish and English translations
- 60-second update interval for near-real-time stream monitoring

---

## Sensors

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.tautulli_total_movies` | `int` | Total number of movies across all movie libraries |
| `sensor.tautulli_total_tv_shows` | `int` | Total number of TV shows (not seasons or episodes) |
| `sensor.tautulli_active_streams` | `int` | Number of currently active streams |
| `sensor.tautulli_streams_7_days` | `int` | Total play count over the last 7 days |
| `sensor.tautulli_streams_30_days` | `int` | Total play count over the last 30 days |

### Extra Attributes

**Active Streams** includes:
- `sessions`: list of active sessions with `user`, `title`, `media_type` (movie/episode), `player`, `state`, `progress_percent`
- `movie_streams`: count of active movie streams
- `episode_streams`: count of active episode/TV streams

**Total Movies / Total TV Shows** includes:
- `libraries`: breakdown of count per library name

**Streams (7/30 Days)** includes:
- `daily`: date-keyed breakdown of daily play counts

---

## Installation via HACS

1. In Home Assistant, go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/macokay/hacs-tautulli-extended` as category **Integration**
3. Find **Tautulli Extended** in HACS and click **Download**
4. Restart Home Assistant

### Manual installation

Copy the `custom_components/tautulli_extended` folder into your `config/custom_components/` directory and restart.

---

## Configuration

After installation:

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Tautulli Extended**
3. Enter your **Tautulli URL** (e.g. `http://192.168.1.100:8181`) and **API key**
4. Click **Submit**

Your Tautulli API key can be found in **Tautulli → Settings → Web Interface → API key**.

---

## Data source

Data is fetched from your local [Tautulli](https://tautulli.com/) instance via its API. Tautulli must be installed and running alongside your Plex Media Server.

---

## Requirements

- A running [Tautulli](https://tautulli.com/) instance with API access
- Tautulli API key
- Home Assistant 2023.1.0 or newer

---

## Known limitations

- Library counts update when Tautulli scans libraries (not instantly when new media is added)
- Play counts depend on Tautulli's recorded history — if Tautulli was recently installed, historical data may be incomplete

---

## Credits

Built by [Mac O Kay](https://github.com/macokay). Data provided by [Tautulli](https://tautulli.com/).

---

## License

© 2026 Mac O Kay
Free to use and modify for personal, non-commercial use.
Credit appreciated if you share or build upon this work.
Commercial use is not permitted.
