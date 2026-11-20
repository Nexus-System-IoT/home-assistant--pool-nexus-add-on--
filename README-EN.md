# Nexus System Local

Your Nexus System devices (Pool Nexus, and the next products) in Home Assistant, **on your local
network**, without going through the Nexus System cloud.

[Version française](README.md)

## How it works

Each Nexus System device publishes Home Assistant discovery itself on **your** MQTT broker: Home
Assistant creates the device and all its entities (readings, status, alerts, settings, controls),
in the device's language, through the **MQTT** integration. Nothing to declare by hand, and a new
firmware brings its new entities by itself.

The **Nexus System Local** integration recognises these devices, whatever the product, and adds:

| Addition | Use |
|---|---|
| **Local link** (binary sensor, one per device) | Online / offline on the broker, for automations and alerts. |
| **"Send to a Nexus device" action** (`nexus_system_local.send`) | Send a setting or a command; the device applies the same checks as the app. |
| **`nexus_system_local_result` event** | The device's answer to each send. |
| **Repair** | Warns when MQTT discovery is disabled (entities would not appear). |
| **Diagnostics** | The devices seen, their firmware and MQTT topic. |

## Installation

1. **MQTT broker**: install the **Mosquitto** add-on, create a user for your devices and enable the
   **TLS** listener (port 8883) with your certificate.
2. Home Assistant **MQTT integration**, discovery enabled (the default).
3. **In the Nexus System app**: open the device, *Local configuration* (or the Bluetooth setup),
   set the broker (address, port, user, password, TLS). The device shows up in Home Assistant
   within seconds.
4. **Nexus System Local**: HACS › Custom repositories › this repository (*Integration*), install,
   restart Home Assistant, then Settings › Devices & services › Add › *Nexus System Local*. The
   assistant lists the devices found on the broker.

One setup follows every Nexus System device on the broker.

## Examples

Turn on a Pool Nexus's lights:

```yaml
action: nexus_system_local.send
data:
  device_id: <your device>
  data:
    outputs:
      lights: true
```

The keys each device accepts, the entities created and the security rules (unencrypted broker:
only the lights stay controllable) are described in the Nexus System "Local mode, local MQTT and
Home Assistant" documentation.

## Coming from the old "PoolNexus" integration

The old integration (`poolnexus`) listened to `poolnexus/<serial>/…` topics the devices no longer
publish. Remove it (Settings › Devices & services › PoolNexus › Delete), then follow the
installation above.

## Development

```bash
python3 tests/test_discovery.py
pip install pytest-homeassistant-custom-component && pytest
```
