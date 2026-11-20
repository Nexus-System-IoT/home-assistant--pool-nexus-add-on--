"""Assistant d'ajout : vérifie MQTT et montre les appareils Nexus System vus sur le broker."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import callback

from .const import DISCOVERY_TOPIC, DOMAIN, SCAN_SECONDS
from .discovery import parse_discovery


class NexusSystemLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Une seule entrée : elle suit tous les appareils Nexus System du broker."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if not self.hass.config_entries.async_entries("mqtt"):
            return self.async_abort(reason="mqtt_required")
        if user_input is not None:
            return self.async_create_entry(title="Nexus System Local", data={})

        found: dict[str, str] = {}

        @callback
        def collect(msg: mqtt.ReceiveMessage) -> None:
            device = parse_discovery(msg.topic, msg.payload)
            if device is not None:
                found[device.device_id] = f"{device.name} ({device.model})" if device.model else device.name

        # Les messages de découverte sont retenus : quelques secondes suffisent à tous les recevoir.
        unsub = await mqtt.async_subscribe(self.hass, DISCOVERY_TOPIC, collect, 0)
        await asyncio.sleep(SCAN_SECONDS)
        unsub()
        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "count": str(len(found)),
                "devices": "\n".join(f"- {n}" for n in sorted(found.values())) or "-",
            },
        )
