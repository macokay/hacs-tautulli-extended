"""Sensors for Tautulli Extended."""
import asyncio
import logging
from datetime import timedelta

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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tautulli Extended sensors from config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    url = config[CONF_URL]
    api_key = config[CONF_API_KEY]

    coordinator = TautulliCoordinator(hass, url, api_key)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        TautulliTotalMoviesSensor(coordinator, entry),
        TautulliTotalShowsSensor(coordinator, entry),
        TautulliActiveStreamsSensor(coordinator, entry),
        TautulliStreams7dSensor(coordinator, entry),
        TautulliStreams30dSensor(coordinator, entry),
    ])


class TautulliCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches data from the Tautulli API."""

    def __init__(self, hass: HomeAssistant, url: str, api_key: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tautulli Extended",
            update_interval=SCAN_INTERVAL,
        )
        self._url = url
        self._api_key = api_key
        self._session = async_get_clientsession(hass)

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
            libraries, activity, plays = await asyncio.gather(
                self._api_call("get_libraries"),
                self._api_call("get_activity"),
                self._api_call("get_plays_by_date", {"time_range": "30"}),
            )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with Tautulli: {err}") from err

        # --- Libraries: sum movies and shows ---
        total_movies = 0
        total_shows = 0
        movie_libraries = {}
        show_libraries = {}

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

        # --- Activity: active streams ---
        stream_count = int(activity.get("stream_count", 0))
        sessions = []
        for s in activity.get("sessions", []):
            sessions.append({
                "user": s.get("user", "Unknown"),
                "title": s.get("full_title", "Unknown"),
                "media_type": s.get("media_type", "Unknown"),
                "player": s.get("player", "Unknown"),
                "state": s.get("state", "Unknown"),
                "progress_percent": s.get("progress_percent", "0"),
            })

        # --- Plays by date: 7d and 30d ---
        # plays.categories = list of date strings
        # plays.series = list of dicts with "name" (library) and "data" (daily counts)
        categories = plays.get("categories", [])
        series_list = plays.get("series", [])

        # Sum all libraries' daily counts into a single daily total
        daily_totals = [0] * len(categories)
        for series in series_list:
            for i, count in enumerate(series.get("data", [])):
                daily_totals[i] += int(count)

        streams_30d = sum(daily_totals)
        streams_7d = sum(daily_totals[-7:]) if len(daily_totals) >= 7 else sum(daily_totals)

        # Build daily breakdown dicts for attributes
        daily_breakdown_30d = dict(zip(categories, daily_totals))
        daily_breakdown_7d = dict(zip(categories[-7:], daily_totals[-7:]))

        return {
            "total_movies": total_movies,
            "total_shows": total_shows,
            "movie_libraries": movie_libraries,
            "show_libraries": show_libraries,
            "stream_count": stream_count,
            "sessions": sessions,
            "streams_7d": streams_7d,
            "streams_30d": streams_30d,
            "daily_breakdown_7d": daily_breakdown_7d,
            "daily_breakdown_30d": daily_breakdown_30d,
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
        """Return device info to group all sensors under one device."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Tautulli",
            "manufacturer": "Tautulli",
            "entry_type": "service",
        }


class TautulliTotalMoviesSensor(TautulliBaseSensor):
    """Sensor for total number of movies across all libraries."""

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
    """Sensor for total number of TV shows across all libraries."""

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


class TautulliActiveStreamsSensor(TautulliBaseSensor):
    """Sensor for number of active streams with per-stream details."""

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
        sessions = self.coordinator.data.get("sessions", [])
        return {
            "sessions": sessions,
            "movie_streams": sum(
                1 for s in sessions if s.get("media_type") == "movie"
            ),
            "episode_streams": sum(
                1 for s in sessions if s.get("media_type") == "episode"
            ),
        }


class TautulliStreams7dSensor(TautulliBaseSensor):
    """Sensor for total streams in the last 7 days."""

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
    """Sensor for total streams in the last 30 days."""

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
