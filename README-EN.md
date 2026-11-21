<p align="center">
  <img src="custom_components/nexus_system_local/brand/icon@2x.png" width="140" alt="Nexus System">
</p>

<h1 align="center">Nexus System Local — Home Assistant integration</h1>

<p align="center">
  Your <b>Nexus System</b> devices (Pool Nexus, and the next products) in Home Assistant,
  <b>on your local network</b>, without the cloud.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS Custom"></a>
  <img src="https://img.shields.io/github/v/release/Nexus-System-IoT/home-assistant--pool-nexus-add-on--?style=for-the-badge" alt="Release">
  <img src="https://img.shields.io/github/downloads/Nexus-System-IoT/home-assistant--pool-nexus-add-on--/total?style=for-the-badge&label=installs&color=success" alt="Installs">
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.11%2B-049CDB?style=for-the-badge&logo=home-assistant&logoColor=white" alt="HA">
</p>

[Version française](README.md)

---

## ✨ Features

Each Nexus System device publishes Home Assistant discovery **itself** on your MQTT broker: Home
Assistant creates the device and all its entities, in the device's language, with nothing to
declare by hand. A firmware update brings its new entities by itself.

For a **Pool Nexus**, one "Pool Nexus &lt;serial&gt;" device with:

| Group | Entities | Type |
| --- | --- | --- |
| Readings | pH, ORP (mV), water temperature, pressure 1 and 2 (if fitted), raw probe mV | `sensor` |
| Water and products | water level low, pH- and chlorine tanks (level and alert), filtration flow, frost guard, filling | `sensor`, `binary_sensor` |
| Dosing | pH- and chlorine dosing pumps, amounts dosed over 24 h, last dose, run times | `sensor`, `binary_sensor` |
| Probes | health, slope, offset, last calibration, probe not calibrated | `sensor`, `binary_sensor` |
| Alerts | active alerts, then one entity per alert (probe, flow, tank, dosing blocked, certificate…) | `sensor`, `binary_sensor` |
| Controls | filtration, light 1, light 2; filtration mode; pH and chlorine regulation, automatic filling | `switch`, `select` |
| Settings | pH and ORP targets, local measurement interval, heat pump connected, variable-speed pump | `number`, `switch` |
| Pauses | pause / resume regulation or filtration for 24 h | `button` |
| Information | wintering, pool volume, pressure sensors, minimum pressure, filtration planned today | `sensor` |
| Diagnostics | firmware (update), Wi-Fi, network link, IP address, uptime, last restart cause, cloud, Matter, last command | `update`, `sensor`, `binary_sensor` |

The **Nexus System Local** integration recognises these devices, whatever the product, and adds:

| Addition | Type | Detail |
| --- | --- | --- |
| Local link | `binary_sensor` (connectivity) | online / offline on the broker, one per device |
| Send to a Nexus device | action `nexus_system_local.send` | setting or command; the device applies the same checks as the app |
| Device answer | event `nexus_system_local_result` | the result of each send (`ok`, `error`) |
| MQTT discovery disabled | repair | warns: without it, no entity appears |
| Diagnostics | downloadable | devices seen, firmware, MQTT topic |

> 🔒 Nothing goes through the Nexus System cloud. With an **unencrypted** broker, the device only
> accepts the lights; everything else is read-only.

---

## 📦 Installation

### 1. MQTT broker

1. Install the **Mosquitto broker** add-on.
2. Create a user for your devices and enable the **TLS** listener (port 8883) with your certificate.
3. Add the Home Assistant **MQTT** integration (discovery enabled, the default).

### 2. The device

In the **Nexus System** app: open the device › **Local configuration** (or the Bluetooth setup) ›
set the broker: address, port, user, password, TLS. The device shows up in Home Assistant within
seconds.

### 3. Nexus System Local via HACS (recommended)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Nexus-System-IoT&repository=home-assistant--pool-nexus-add-on--&category=integration)

1. Click the button above **or**: HACS › ⋮ menu (top right) › **Custom repositories**
2. URL: `https://github.com/Nexus-System-IoT/home-assistant--pool-nexus-add-on--` — category: **Integration**
3. Open **Nexus System Local** › **Download**
4. **Restart** Home Assistant

### Manual

Copy `custom_components/nexus_system_local/` into `config/custom_components/`, then restart.

---

## ⚙️ Configuration

[![Add the integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=nexus_system_local)

*Settings › Devices & services › **Add integration** › "Nexus System Local"*. The assistant checks
MQTT and lists the devices found on the broker. One setup follows every Nexus System device on the
broker, including ones added later.

---

## 🤖 Examples

### Turn on the lights

```yaml
action: nexus_system_local.send
data:
  device_id: <your device>
  data:
    outputs:
      lights: true
```

### Get notified when the Pool Nexus stops answering

```yaml
automation:
  - alias: Pool Nexus - link lost
    triggers:
      - trigger: state
        entity_id: binary_sensor.pool_nexus_pn0000001_local_link
        to: "off"
        for: { minutes: 5 }
    actions:
      - action: notify.notify
        data:
          title: Pool Nexus
          message: "The Pool Nexus no longer answers on the local network."
```

### Follow the device's answer

```yaml
automation:
  - alias: Nexus - setting refused
    triggers:
      - trigger: event
        event_type: nexus_system_local_result
    conditions:
      - condition: template
        value_template: "{{ trigger.event.data.result.ok is false }}"
    actions:
      - action: persistent_notification.create
        data:
          title: "Nexus {{ trigger.event.data.serial }}"
          message: "Setting refused: {{ trigger.event.data.result.error }}"
```

> Replace `pn0000001` with your device's serial number (visible in the generated entity id).

Accepted keys, every entity and the MQTT topics are described in the
[local MQTT documentation](https://developer.nexus-system.fr/docs?page=MQTT%20local%20et%20domotique)
and the [Home Assistant guide](https://developer.nexus-system.fr/integrations/home-assistant).

---

## 🔁 Coming from the old "PoolNexus" integration

The old integration (`poolnexus`) listened to `poolnexus/<serial>/…` topics the devices no longer
publish. Remove it (Settings › Devices & services › PoolNexus › Delete), then follow the
installation above.

---

## 📊 Adoption

- 🔢 **installs** badge (top): cumulative downloads of the `.zip` asset counted by GitHub (installs and updates).
- 📈 **HA Analytics** (active installs): [analytics.home-assistant.io/custom_integrations](https://analytics.home-assistant.io/custom_integrations/) › domain `nexus_system_local`, updated weekly.

<p align="center">
  <a href="https://star-history.com/#Nexus-System-IoT/home-assistant--pool-nexus-add-on--&Date">
    <img src="https://api.star-history.com/svg?repos=Nexus-System-IoT/home-assistant--pool-nexus-add-on--&type=Date" width="600" alt="Star History Chart">
  </a>
</p>

---

## 🤝 Contributing

- 🐛 **Bug**: open an [issue](https://github.com/Nexus-System-IoT/home-assistant--pool-nexus-add-on--/issues) with your Home Assistant and firmware versions and the logs (`custom_components.nexus_system_local`); the integration's diagnostics help a lot.
- 💡 **Idea**: open an issue to discuss it before coding.
- 🔧 **Pull request**: fork, branch, open a PR to `main`.

### Development

```bash
python3 tests/test_discovery.py
pip install pytest-homeassistant-custom-component && pytest
```

### Releasing

Bump `version` in `manifest.json`, then push the `v<version>` tag: the GitHub release and the
`nexus_system_local.zip` asset (installed by HACS) are created automatically.
