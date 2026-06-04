"""Sensors for Tautulli Extended."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_API_KEY, CONF_URL, DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL_SECONDS)


def _parse_plays_data(plays: dict) -> dict:
    """Compute 7d/30d/365d/this-year totals from a get_plays_by_date response."""
    categories = plays.get("categories", [])
    daily = [0] * len(categories)
    for s in plays.get("series", []):
        for i, c in enumerate(s.get("data", [])):
            daily[i] += int(c)

    year_start = f"{datetime.now().year}-01-01"
    this_year_total = 0
    this_year_daily: dict = {}
    for date_str, total in zip(categories, daily):
        if date_str >= year_start:
            this_year_total += total
            this_year_daily[date_str] = total

    return {
        "total_365d": sum(daily),
        "total_30d": sum(daily[-30:]) if len(daily) >= 30 else sum(daily),
        "total_7d": sum(daily[-7:]) if len(daily) >= 7 else sum(daily),
        "total_this_year": this_year_total,
        "daily_365d": dict(zip(categories, daily)),
        "daily_30d": dict(zip(categories[-30:], daily[-30:])),
        "daily_7d": dict(zip(categories[-7:], daily[-7:])),
        "daily_this_year": this_year_daily,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tautulli Extended sensors from config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    coordinator = TautulliCoordinator(hass, config[CONF_URL], config[CONF_API_KEY])
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            TautulliTotalMoviesSensor(coordinator, entry),
            TautulliTotalShowsSensor(coordinator, entry),
            TautulliActiveStreamsSensor(coordinator, entry),
            TautulliActiveStreamTypeSensor(coordinator, entry),
            TautulliStreams7dSensor(coordinator, entry),
            TautulliStreams30dSensor(coordinator, entry),
            TautulliStreams365dSensor(coordinator, entry),
            TautulliStreamsThisYearSensor(coordinator, entry),
            # Optional per-media-type stream sensors (disabled by default)
            TautulliMovieStreams7dSensor(coordinator, entry),
            TautulliMovieStreams30dSensor(coordinator, entry),
            TautulliMovieStreams365dSensor(coordinator, entry),
            TautulliMovieStreamsThisYearSensor(coordinator, entry),
            TautulliSeriesStreams7dSensor(coordinator, entry),
            TautulliSeriesStreams30dSensor(coordinator, entry),
            TautulliSeriesStreams365dSensor(coordinator, entry),
            TautulliSeriesStreamsThisYearSensor(coordinator, entry),
        ]
    )


class TautulliCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches data from the Tautulli API."""

    def __init__(self, hass: HomeAssistant, url: str, api_key: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass, _LOGGER, name="Tautulli Extended", update_interval=SCAN_INTERVAL
        )
        self._url = url
        self._api_key = api_key
        self._session = async_get_clientsession(hass)
        self._library_cache: dict = {}

    async def _api_call(self, cmd: str, params: dict | None = None) -> dict:
        """Make a single API call to Tautulli."""
        request_params = {"apikey": self._api_key, "cmd": cmd}
        if params:
            request_params.update(params)
        resp = await self._session.get(
            f"{self._url}/api/v2",
            params=request_params,
            timeout=aiohttp.ClientTimeout(total=15),
        )
        resp.raise_for_status()
        data = await resp.json(content_type=None)
        if data.get("response", {}).get("result") != "success":
            raise UpdateFailed(
                f"Tautulli API error for {cmd}: "
                f"{data.get('response', {}).get('message', 'Unknown error')}"
            )
        return data["response"]["data"]

    async def _async_update_data(self) -> dict:
        """Fetch latest data from the Tautulli API."""
        try:
            (
                libraries,
                activity,
                plays,
                movie_plays,
                episode_plays,
            ) = await asyncio.gather(
                self._api_call("get_libraries"),
                self._api_call("get_activity"),
                self._api_call("get_plays_by_date", {"time_range": "365"}),
                self._api_call(
                    "get_plays_by_date", {"time_range": "365", "media_type": "movie"}
                ),
                self._api_call(
                    "get_plays_by_date", {"time_range": "365", "media_type": "episode"}
                ),
            )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with Tautulli: {err}") from err

        # Libraries — fall back to cached counts when Plex is offline and Tautulli returns 0
        total_movies = 0
        total_shows = 0
        movie_libraries: dict = {}
        show_libraries: dict = {}

        for lib in libraries:
            section_type = lib.get("section_type", "")
            name = lib.get("section_name", "Unknown")
            count = int(lib.get("count", 0))
            if section_type == "movie":
                total_movies += count
                movie_libraries[name] = count
            elif section_type == "show":
                total_shows += count
                show_libraries[name] = count

        if total_movies == 0 and self._library_cache.get("total_movies", 0) > 0:
            total_movies = self._library_cache["total_movies"]
            movie_libraries = self._library_cache.get("movie_libraries", {})
        if total_shows == 0 and self._library_cache.get("total_shows", 0) > 0:
            total_shows = self._library_cache["total_shows"]
            show_libraries = self._library_cache.get("show_libraries", {})

        if total_movies > 0 or total_shows > 0:
            self._library_cache = {
                "total_movies": total_movies,
                "movie_libraries": movie_libraries,
                "total_shows": total_shows,
                "show_libraries": show_libraries,
            }

        # Activity
        stream_count = int(activity.get("stream_count", 0))
        sessions = []
        for s in activity.get("sessions", []):
            sessions.append(
                {
                    "user": s.get("user", "Unknown"),
                    "title": s.get("full_title", "Unknown"),
                    "media_type": s.get("media_type", "Unknown"),
                    "player": s.get("player", "Unknown"),
                    "state": s.get("state", "Unknown"),
                    "progress_percent": s.get("progress_percent", "0"),
                }
            )

        movie_streams = sum(1 for s in sessions if s["media_type"] == "movie")
        episode_streams = sum(1 for s in sessions if s["media_type"] == "episode")

        if stream_count == 0:
            stream_type = "Idle"
        elif movie_streams > 0 and episode_streams > 0:
            stream_type = "Mixed"
        elif movie_streams > 0:
            stream_type = "Movie"
        elif episode_streams > 0:
            stream_type = "TV Show"
        else:
            stream_type = "Other"

        # Plays by date
        p = _parse_plays_data(plays)
        mp = _parse_plays_data(movie_plays)
        ep = _parse_plays_data(episode_plays)

        return {
            "total_movies": total_movies,
            "total_shows": total_shows,
            "movie_libraries": movie_libraries,
            "show_libraries": show_libraries,
            "stream_count": stream_count,
            "sessions": sessions,
            "stream_type": stream_type,
            "movie_streams": movie_streams,
            "episode_streams": episode_streams,
            "streams_7d": p["total_7d"],
            "streams_30d": p["total_30d"],
            "streams_365d": p["total_365d"],
            "streams_this_year": p["total_this_year"],
            "daily_breakdown_7d": p["daily_7d"],
            "daily_breakdown_30d": p["daily_30d"],
            "daily_breakdown_365d": p["daily_365d"],
            "daily_breakdown_this_year": p["daily_this_year"],
            "movie_streams_7d": mp["total_7d"],
            "movie_streams_30d": mp["total_30d"],
            "movie_streams_365d": mp["total_365d"],
            "movie_streams_this_year": mp["total_this_year"],
            "episode_streams_7d": ep["total_7d"],
            "episode_streams_30d": ep["total_30d"],
            "episode_streams_365d": ep["total_365d"],
            "episode_streams_this_year": ep["total_this_year"],
        }


class TautulliBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Tautulli sensors."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: TautulliCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Tautulli Extended",
            "manufacturer": "by macokay",
            "entry_type": "service",
        }


# --- Library sensors ---


class TautulliTotalMoviesSensor(TautulliBaseSensor):
    _attr_name = "Total Movies"
    _attr_icon = "mdi:filmstrip"
    _attr_native_unit_of_measurement = "movies"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_movies"

    @property
    def native_value(self):
        return self.coordinator.data.get("total_movies")

    @property
    def extra_state_attributes(self):
        return {"libraries": self.coordinator.data.get("movie_libraries", {})}


class TautulliTotalShowsSensor(TautulliBaseSensor):
    _attr_name = "Total TV Shows"
    _attr_icon = "mdi:television-classic"
    _attr_native_unit_of_measurement = "shows"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_shows"

    @property
    def native_value(self):
        return self.coordinator.data.get("total_shows")

    @property
    def extra_state_attributes(self):
        return {"libraries": self.coordinator.data.get("show_libraries", {})}


# --- Activity sensors ---


class TautulliActiveStreamsSensor(TautulliBaseSensor):
    _attr_name = "Active Streams"
    _attr_icon = "mdi:play-network"
    _attr_native_unit_of_measurement = "streams"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active_streams"

    @property
    def native_value(self):
        return self.coordinator.data.get("stream_count")

    @property
    def extra_state_attributes(self):
        return {
            "sessions": self.coordinator.data.get("sessions", []),
            "movie_streams": self.coordinator.data.get("movie_streams", 0),
            "episode_streams": self.coordinator.data.get("episode_streams", 0),
        }


class TautulliActiveStreamTypeSensor(TautulliBaseSensor):
    _attr_name = "Active Stream Type"
    _attr_icon = "mdi:filmstrip-box-multiple"
    _attr_state_class = None

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active_stream_type"

    @property
    def native_value(self):
        return self.coordinator.data.get("stream_type", "Idle")

    @property
    def extra_state_attributes(self):
        return {
            "movie_streams": self.coordinator.data.get("movie_streams", 0),
            "episode_streams": self.coordinator.data.get("episode_streams", 0),
            "sessions": self.coordinator.data.get("sessions", []),
        }


# --- Total stream stats ---


class TautulliStreams7dSensor(TautulliBaseSensor):
    _attr_name = "Streams (7 Days)"
    _attr_icon = "mdi:chart-bar"
    _attr_native_unit_of_measurement = "plays"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_streams_7d"

    @property
    def native_value(self):
        return self.coordinator.data.get("streams_7d")

    @property
    def extra_state_attributes(self):
        return {"daily": self.coordinator.data.get("daily_breakdown_7d", {})}


class TautulliStreams30dSensor(TautulliBaseSensor):
    _attr_name = "Streams (30 Days)"
    _attr_icon = "mdi:chart-bar"
    _attr_native_unit_of_measurement = "plays"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_streams_30d"

    @property
    def native_value(self):
        return self.coordinator.data.get("streams_30d")

    @property
    def extra_state_attributes(self):
        return {"daily": self.coordinator.data.get("daily_breakdown_30d", {})}


class TautulliStreams365dSensor(TautulliBaseSensor):
    _attr_name = "Streams (1 Year)"
    _attr_icon = "mdi:chart-bar"
    _attr_native_unit_of_measurement = "plays"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_streams_365d"

    @property
    def native_value(self):
        return self.coordinator.data.get("streams_365d")

    @property
    def extra_state_attributes(self):
        return {"daily": self.coordinator.data.get("daily_breakdown_365d", {})}


class TautulliStreamsThisYearSensor(TautulliBaseSensor):
    _attr_name = "Streams (This Year)"
    _attr_icon = "mdi:calendar-check"
    _attr_native_unit_of_measurement = "plays"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_streams_this_year"

    @property
    def native_value(self):
        return self.coordinator.data.get("streams_this_year")

    @property
    def extra_state_attributes(self):
        return {"daily": self.coordinator.data.get("daily_breakdown_this_year", {})}


# --- Optional per-media-type stream sensors (disabled by default) ---


class _OptionalStreamSensor(TautulliBaseSensor):
    """Base for optional per-media-type stream sensors."""

    _attr_icon = "mdi:chart-bar"
    _attr_native_unit_of_measurement = "plays"
    _attr_entity_registry_enabled_default = False
    _data_key: str

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{self._data_key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)


class TautulliMovieStreams7dSensor(_OptionalStreamSensor):
    _attr_name = "Movie Streams (7 Days)"
    _data_key = "movie_streams_7d"


class TautulliMovieStreams30dSensor(_OptionalStreamSensor):
    _attr_name = "Movie Streams (30 Days)"
    _data_key = "movie_streams_30d"


class TautulliMovieStreams365dSensor(_OptionalStreamSensor):
    _attr_name = "Movie Streams (1 Year)"
    _data_key = "movie_streams_365d"


class TautulliMovieStreamsThisYearSensor(_OptionalStreamSensor):
    _attr_name = "Movie Streams (This Year)"
    _attr_icon = "mdi:calendar-check"
    _data_key = "movie_streams_this_year"


class TautulliSeriesStreams7dSensor(_OptionalStreamSensor):
    _attr_name = "Series Streams (7 Days)"
    _data_key = "episode_streams_7d"


class TautulliSeriesStreams30dSensor(_OptionalStreamSensor):
    _attr_name = "Series Streams (30 Days)"
    _data_key = "episode_streams_30d"


class TautulliSeriesStreams365dSensor(_OptionalStreamSensor):
    _attr_name = "Series Streams (1 Year)"
    _data_key = "episode_streams_365d"


class TautulliSeriesStreamsThisYearSensor(_OptionalStreamSensor):
    _attr_name = "Series Streams (This Year)"
    _attr_icon = "mdi:calendar-check"
    _data_key = "episode_streams_this_year"
