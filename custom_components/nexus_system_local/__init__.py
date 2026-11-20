"""Nexus System Local : les appareils Nexus System dans Home Assistant, sur le réseau local.

Les appareils publient eux-mêmes leur découverte Home Assistant sur votre broker MQTT : toutes
leurs entités (mesures, état, alertes, réglages, commandes) sont créées par l'intégration MQTT.
Cette intégration les reconnaît, quel que soit le produit (Pool Nexus et les suivants), et ajoute
ce que la découverte ne donne pas :

- la liaison locale de chaque appareil (en ligne / hors ligne), utilisable dans les automatisations ;
- l'action « nexus_system_local.send » pour envoyer une commande ou un réglage à un appareil
  (l'appareil applique les mêmes contrôles que l'app), et l'évènement « nexus_system_local_result »
  avec sa réponse ;
- une réparation si la découverte MQTT est désactivée (les entités n'apparaîtraient pas) ;
- un diagnostic qui liste les appareils vus.

Rien ne passe par le cloud Nexus System.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType

from .const import (
    DISCOVERY_TOPIC,
    DOMAIN,
    EVENT_RESULT,
    LWT_SUFFIX,
    RESULT_SUFFIX,
    SERVICE_SEND,
    SET_SUFFIX,
    SIGNAL_DEVICE_UPDATE,
    SIGNAL_NEW_DEVICE,
)
from .discovery import NexusDevice, parse_discovery

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SEND_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("data"): vol.All(dict, vol.Length(min=1)),
    }
)

type NexusConfigEntry = ConfigEntry[NexusHub]


class NexusHub:
    """Les appareils Nexus System vus sur le broker, et leur liaison."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.devices: dict[str, NexusDevice] = {}
        self.online: dict[str, bool | None] = {}
        self._unsubs: list[Any] = []

    async def async_start(self) -> None:
        self._unsubs.append(await mqtt.async_subscribe(self.hass, DISCOVERY_TOPIC, self._on_discovery, 0))

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    @callback
    def _on_discovery(self, msg: mqtt.ReceiveMessage) -> None:
        device = parse_discovery(msg.topic, msg.payload)
        if device is None:
            return
        known = self.devices.get(device.device_id)
        if known is not None:
            if known.merge(device):
                async_dispatcher_send(self.hass, SIGNAL_DEVICE_UPDATE.format(device.device_id))
            return
        self.devices[device.device_id] = device
        self.online[device.device_id] = None
        _LOGGER.info("Appareil Nexus System trouvé : %s (%s)", device.name, device.base_topic)
        self.hass.async_create_task(self._async_watch(device))
        async_dispatcher_send(self.hass, SIGNAL_NEW_DEVICE, device)

    async def _async_watch(self, device: NexusDevice) -> None:
        @callback
        def on_lwt(msg: mqtt.ReceiveMessage) -> None:
            payload = msg.payload.decode() if isinstance(msg.payload, bytes) else msg.payload
            self.online[device.device_id] = payload == "online"
            async_dispatcher_send(self.hass, SIGNAL_DEVICE_UPDATE.format(device.device_id))

        @callback
        def on_result(msg: mqtt.ReceiveMessage) -> None:
            try:
                result = json.loads(msg.payload)
            except ValueError:
                result = {"raw": str(msg.payload)}
            self.hass.bus.async_fire(EVENT_RESULT, {"device": device.device_id, "serial": device.serial, "result": result})

        self._unsubs.append(await mqtt.async_subscribe(self.hass, device.base_topic + LWT_SUFFIX, on_lwt, 0))
        self._unsubs.append(await mqtt.async_subscribe(self.hass, device.base_topic + RESULT_SUFFIX, on_result, 0))

    def device_for(self, ha_device_id: str) -> NexusDevice:
        """L'appareil Nexus derrière un identifiant d'appareil Home Assistant."""
        entry = dr.async_get(self.hass).async_get(ha_device_id)
        if entry is not None:
            for domain, ident in entry.identifiers:
                if domain in ("mqtt", DOMAIN) and ident in self.devices:
                    return self.devices[ident]
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="unknown_device", translation_placeholders={"device": ha_device_id}
        )


def _check_mqtt_discovery(hass: HomeAssistant) -> None:
    """Sans la découverte MQTT, les entités des appareils n'apparaissent pas : on le signale."""
    disabled = any(not {**e.data, **e.options}.get("discovery", True) for e in hass.config_entries.async_entries("mqtt"))
    if disabled:
        ir.async_create_issue(
            hass, DOMAIN, "mqtt_discovery_disabled", is_fixable=False, severity=ir.IssueSeverity.WARNING,
            translation_key="mqtt_discovery_disabled",
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, "mqtt_discovery_disabled")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """L'action « send » : un objet JSON publié sur « <base>/local/set » de l'appareil."""

    async def send(call: ServiceCall) -> None:
        entries = [e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED]
        if not entries:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="not_loaded")
        device = entries[0].runtime_data.device_for(call.data["device_id"])
        await mqtt.async_publish(hass, device.base_topic + SET_SUFFIX, json.dumps(call.data["data"]), 1, False)

    hass.services.async_register(DOMAIN, SERVICE_SEND, send, schema=SEND_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: NexusConfigEntry) -> bool:
    if not await mqtt.async_wait_for_mqtt_client(hass):
        _LOGGER.error("MQTT indisponible : Nexus System Local attend l'intégration MQTT")
        return False
    _check_mqtt_discovery(hass)
    hub = NexusHub(hass)
    entry.runtime_data = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await hub.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NexusConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded
