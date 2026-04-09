<p align="center">
  <img src="custom_components/tautulli_extended/brand/icon.svg" alt="Tautulli Extended" width="120" />
</p>

<h1 align="center">Tautulli Extended</h1>

<p align="center">
  Detailed Plex media server statistics in Home Assistant — library counts, active streams with media type detection, and play counts over multiple time ranges.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration">
    <img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS Custom" />
  </a>
  <a href="https://github.com/macokay/hacs-tautulli-extended/releases">
    <img src="https://img.shields.io/github/v/release/macokay/hacs-tautulli-extended" alt="GitHub release" />
  </a>
  <a href="https://github.com/macokay/hacs-tautulli-extended/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-Non--Commercial-blue.svg" alt="License" />
  </a>
</p>

<p align="center">
  <a href="https://www.buymeacoffee.com/macokay">
    <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-%23FFDD00.svg?logo=buy-me-a-coffee&logoColor=black" alt="Buy Me A Coffee" />
  </a>
</p>

---

## Features

- **Total movies** across all Plex movie libraries (auto-summed)
- **Total TV shows** across all Plex show libraries (show count, not seasons or episodes)
- **Active streams** — live count of concurrent streams
- **Active stream type** — shows whether active streams are Movie, TV Show, Mixed, or Idle
- **Streams last 7 days** with daily breakdown
- **Streams last 30 days** with daily breakdown
- **Streams last year** (365 days) with daily breakdown
- **Streams this year** (current calendar year) with daily breakdown
- GUI config flow — no YAML needed
- Danish and English translations
- 60-second update interval for near-real-time stream monitoring

---

## Requirements

| Requirement | Version / Details |
|---|---|
| Home Assistant | 2023.1 or newer |
| Tautulli | Running instance with API access enabled |
| Tautulli API key | Found in **Tautulli → Settings → Web Interface → API key** |

---

## Installation

### Automatic — via HACS

1. Open **HACS** in Home Assistant.
2. Go to **Integrations** → three-dot menu (⋮) → **Custom repositories**.
3. Add `https://github.com/macokay/hacs-tautulli-extended` as **Integration**.
4. Search for **Tautulli Extended** and click **Download**.
5. Restart Home Assistant.

### Manual

1. Download the latest release from [GitHub Releases](https://github.com/macokay/hacs-tautulli-extended/releases).
2. Copy the `custom_components/tautulli_extended` folder to your `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Tautulli Extended**.
3. Enter the required fields:

| Field | Description |
|---|---|
| Tautulli URL | Base URL of your Tautulli instance (e.g. `http://192.168.1.100:8181`) |
| API key | Your Tautulli API key |

The integration tests the connection against the Tautulli API before saving.

---

## Data

### Entities

| Entity | Type | Description |
|---|---|---|
| `sensor.tautulli_total_movies` | `int` | Total movies across all movie libraries |
| `sensor.tautulli_total_tv_shows` | `int` | Total TV shows (not seasons or episodes) |
| `sensor.tautulli_active_streams` | `int` | Number of currently active streams |
| `sensor.tautulli_active_stream_type` | `string` | Movie, TV Show, Mixed, or Idle |
| `sensor.tautulli_streams_7_days` | `int` | Total play count over the last 7 days |
| `sensor.tautulli_streams_30_days` | `int` | Total play count over the last 30 days |
| `sensor.tautulli_streams_1_year` | `int` | Total play count over the last 365 days |
| `sensor.tautulli_streams_this_year` | `int` | Total play count since January 1st |

### Attributes

| Attribute | Available on | Description |
|---|---|---|
| `sessions` | `active_streams`, `active_stream_type` | List of active sessions with `user`, `title`, `media_type`, `player`, `state`, `progress_percent` |
| `movie_streams` | `active_streams`, `active_stream_type` | Count of active movie streams |
| `episode_streams` | `active_streams`, `active_stream_type` | Count of active TV streams |
| `libraries` | `total_movies`, `total_tv_shows` | Count breakdown per library name |
| `daily` | All stream count sensors | Date-keyed breakdown of daily play counts |

### Update interval

Data is fetched every 60 seconds.

---

## Updating

**Via HACS:** HACS will notify you when an update is available. Click **Update** on the integration card.

**Manual:** Replace the `custom_components/tautulli_extended` folder with the new version and restart Home Assistant.

---

## Known Limitations

- Library counts update when Tautulli scans libraries — not instantly when new media is added
- Play counts depend on Tautulli's recorded history — if Tautulli was recently installed, historical data may be incomplete

---

## Credits

- [Tautulli](https://tautulli.com/) — Plex monitoring and statistics application

---

## License

&copy; 2026 Mac O Kay. Free to use and modify for personal, non-commercial use. Attribution appreciated if you share or build upon this work. Commercial use is not permitted.
