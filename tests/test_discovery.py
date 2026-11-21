"""Vérifie la lecture des messages de découverte (sans Home Assistant).

    python3 tests/test_discovery.py
"""

import importlib.util
import json
import pathlib
import sys

spec = importlib.util.spec_from_file_location(
    "discovery", pathlib.Path(__file__).parent.parent / "custom_components/nexus_system_local/discovery.py"
)
discovery = importlib.util.module_from_spec(spec)
sys.modules["discovery"] = discovery
spec.loader.exec_module(discovery)

# Forme publiée par le firmware Pool Nexus (HaDiscovery.hpp).
msg = {
    "dev": {"ids": ["poolnexus_PN0000001"], "name": "Pool Nexus PN0000001", "mf": "Nexus System", "mdl": "Pool Nexus V1",
            "sn": "PN0000001", "sw": "2.7.0"},
    "o": {"name": "Pool Nexus", "sw": "2.7.0"},
    "avty": [{"t": "PoolNexusV1-PN0000001/lwt"}],
    "stat_t": "PoolNexusV1-PN0000001/local/telemetry",
    "cmps": {"ph": {"p": "sensor"}},
}
d = discovery.parse_discovery("homeassistant/device/poolnexus_PN0000001_measures/config", json.dumps(msg))
assert d is not None and d.device_id == "poolnexus_PN0000001" and d.base_topic == "PoolNexusV1-PN0000001"
assert d.model == "Pool Nexus V1" and d.serial == "PN0000001" and d.firmware == "2.7.0" and d.groups == {"measures"}

# Un autre produit Nexus System (même forme) est reconnu ; un autre fabricant, un message vide ou
# illisible, ou sans disponibilité ne l'est pas.
other = json.loads(json.dumps(msg))
other["dev"].update(ids=["gardennexus_GN1"], mdl="Garden Nexus V1")
other["avty"] = [{"topic": "GardenNexusV1-GN1/lwt"}]
g = discovery.parse_discovery("homeassistant/device/gardennexus_GN1_status/config", json.dumps(other).encode())
assert g is not None and g.base_topic == "GardenNexusV1-GN1" and g.groups == {"status"}
foreign = json.loads(json.dumps(msg))
foreign["dev"]["mf"] = "Acme"
assert discovery.parse_discovery("homeassistant/device/x/config", json.dumps(foreign)) is None
assert discovery.parse_discovery("homeassistant/device/x/config", "") is None
assert discovery.parse_discovery("homeassistant/device/x/config", "{nope") is None
assert discovery.parse_discovery("homeassistant/device/x/config", b"\xff") is None
no_avty = json.loads(json.dumps(msg))
del no_avty["avty"]
assert discovery.parse_discovery("homeassistant/device/x/config", json.dumps(no_avty)) is None

# Plusieurs messages du même appareil se fusionnent ; un changement de firmware se voit.
second = json.loads(json.dumps(msg))
second["dev"]["sw"] = "2.7.1"
s = discovery.parse_discovery("homeassistant/device/poolnexus_PN0000001_controls/config", json.dumps(second))
assert d.merge(s) and d.firmware == "2.7.1" and d.groups == {"measures", "controls"}
assert not d.merge(s)

print("test_discovery: OK")
