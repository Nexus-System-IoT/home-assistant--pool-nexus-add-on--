"""Nexus System Local dans un Home Assistant de test (MQTT simulé).

    pip install pytest-homeassistant-custom-component
    pytest tests
"""

import json
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_mqtt_message

from custom_components.nexus_system_local.const import DOMAIN, EVENT_RESULT

DISCOVERY = {
    "dev": {"ids": ["poolnexus_PN0000001"], "name": "Pool Nexus PN0000001", "mf": "Nexus System", "mdl": "Pool Nexus V1",
            "sn": "PN0000001", "sw": "2.7.0"},
    "o": {"name": "Pool Nexus", "sw": "2.7.0"},
    "avty": [{"t": "PoolNexusV1-PN0000001/lwt"}],
    "stat_t": "PoolNexusV1-PN0000001/local/status",
    "cmps": {"cloud_link": {"p": "binary_sensor", "name": "Liaison au cloud", "val_tpl": "{{ value_json.cloud }}", "uniq_id": "poolnexus_PN0000001_cloud"}},
}
TOPIC = "homeassistant/device/poolnexus_PN0000001_status/config"


async def test_device_link_send_and_result(hass: HomeAssistant, mqtt_mock) -> None:
    entry = MockConfigEntry(domain=DOMAIN, title="Nexus System Local", data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, TOPIC, json.dumps(DISCOVERY))
    await hass.async_block_till_done()
    hub = entry.runtime_data
    assert "poolnexus_PN0000001" in hub.devices

    # La liaison suit le lwt, et l'entité se range sous l'appareil créé par la découverte MQTT.
    async_fire_mqtt_message(hass, "PoolNexusV1-PN0000001/lwt", "online")
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.pool_nexus_pn0000001_liaison_locale") or next(
        s for s in hass.states.async_all("binary_sensor") if s.attributes.get("topic") == "PoolNexusV1-PN0000001"
    )
    assert state.state == "on"
    async_fire_mqtt_message(hass, "PoolNexusV1-PN0000001/lwt", "offline")
    await hass.async_block_till_done()
    assert hass.states.get(state.entity_id).state == "off"
    device = dr.async_get(hass).async_get_device(identifiers={("mqtt", "poolnexus_PN0000001")})
    assert device is not None and device.manufacturer == "Nexus System"

    # L'action publie sur <base>/local/set ; la réponse de l'appareil devient un évènement.
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call(DOMAIN, "send", {"device_id": device.id, "data": {"outputs": {"lights": True}}}, blocking=True)
    mqtt_mock.async_publish.assert_called_once_with("PoolNexusV1-PN0000001/local/set", '{"outputs": {"lights": true}}', 1, False)
    events = []
    hass.bus.async_listen(EVENT_RESULT, events.append)
    async_fire_mqtt_message(hass, "PoolNexusV1-PN0000001/local/result", '{"ok": true}')
    await hass.async_block_till_done()
    assert events and events[0].data["result"] == {"ok": True} and events[0].data["serial"] == "PN0000001"

    # Un autre fabricant est ignoré.
    other = json.loads(json.dumps(DISCOVERY))
    other["dev"].update(mf="Acme", ids=["acme_1"])
    async_fire_mqtt_message(hass, "homeassistant/device/acme_1/config", json.dumps(other))
    await hass.async_block_till_done()
    assert "acme_1" not in hub.devices

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_config_flow(hass: HomeAssistant, mqtt_mock) -> None:
    with patch("custom_components.nexus_system_local.config_flow.SCAN_SECONDS", 0):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == "form" and result["description_placeholders"]["count"] == "0"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry" and result["title"] == "Nexus System Local"
    # Une seule entrée.
    with patch("custom_components.nexus_system_local.config_flow.SCAN_SECONDS", 0):
        again = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert again["type"] == "abort" and again["reason"] == "already_configured"


async def test_discovery_disabled_issue(hass: HomeAssistant, mqtt_mock) -> None:
    mqtt_entry = hass.config_entries.async_entries("mqtt")[0]
    hass.config_entries.async_update_entry(mqtt_entry, options={**mqtt_entry.options, "discovery": False})
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, "mqtt_discovery_disabled") is not None
