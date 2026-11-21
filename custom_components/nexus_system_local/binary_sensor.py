"""Liaison locale de chaque appareil Nexus System (en ligne / hors ligne sur le broker)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NexusConfigEntry, NexusHub
from .const import MANUFACTURER, SIGNAL_DEVICE_UPDATE, SIGNAL_NEW_DEVICE
from .discovery import NexusDevice


async def async_setup_entry(hass: HomeAssistant, entry: NexusConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    hub = entry.runtime_data

    @callback
    def add(device: NexusDevice) -> None:
        async_add_entities([NexusLinkSensor(hub, device)])

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, add))
    for device in list(hub.devices.values()):
        add(device)


class NexusLinkSensor(BinarySensorEntity):
    """Vrai tant que l'appareil est connecté au broker (son « lwt » vaut « online »)."""

    _attr_has_entity_name = True
    _attr_translation_key = "local_link"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(self, hub: NexusHub, device: NexusDevice) -> None:
        self._hub = hub
        self._device = device
        self._attr_unique_id = f"{device.device_id}_local_link"
        # Même appareil que celui créé par la découverte MQTT : l'entité s'y range.
        self._attr_device_info = DeviceInfo(
            identifiers={("mqtt", device.device_id)},
            manufacturer=MANUFACTURER,
            model=device.model or None,
            name=device.name,
            serial_number=device.serial or None,
            sw_version=device.firmware or None,
        )

    @property
    def is_on(self) -> bool | None:
        return self._hub.online.get(self._device.device_id)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {"topic": self._device.base_topic, "firmware": self._device.firmware}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_DEVICE_UPDATE.format(self._device.device_id), self.async_write_ha_state)
        )
