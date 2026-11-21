"""Diagnostic : les appareils Nexus System vus sur le broker."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import NexusConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: NexusConfigEntry) -> dict[str, Any]:
    hub = entry.runtime_data
    return {
        "devices": [
            {
                "device_id": d.device_id,
                "name": d.name,
                "model": d.model,
                "firmware": d.firmware,
                "base_topic": d.base_topic,
                "discovery_groups": sorted(d.groups),
                "online": hub.online.get(d.device_id),
            }
            for d in hub.devices.values()
        ]
    }
