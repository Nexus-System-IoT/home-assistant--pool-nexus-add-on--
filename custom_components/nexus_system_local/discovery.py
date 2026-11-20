"""Lecture des messages de découverte Home Assistant publiés par les appareils Nexus System.

Sans dépendance à Home Assistant : vérifié par tests/test_discovery.py.

Chaque appareil publie plusieurs messages retenus (mesures, état, alertes, réglages, commandes),
tous avec le même bloc « dev » (fabricant « Nexus System »). Le sujet de base de l'appareil se lit
dans sa disponibilité : « <base>/lwt ». Un message vide (retrait) ou d'un autre fabricant est ignoré.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

MANUFACTURER = "Nexus System"


@dataclass
class NexusDevice:
    """Un appareil Nexus System vu sur le broker."""

    device_id: str  # identifiant Home Assistant de l'appareil, ex. « poolnexus_PN0000001 »
    name: str
    model: str
    serial: str
    firmware: str
    base_topic: str  # ex. « PoolNexusV1-PN0000001 »
    groups: set[str] = field(default_factory=set)

    def merge(self, other: NexusDevice) -> bool:
        """Reprend les informations d'un autre message du même appareil ; vrai si quelque chose change."""
        changed = False
        for attr in ("name", "model", "serial", "firmware", "base_topic"):
            value = getattr(other, attr)
            if value and value != getattr(self, attr):
                setattr(self, attr, value)
                changed = True
        if not other.groups <= self.groups:
            self.groups |= other.groups
            changed = True
        return changed


def parse_discovery(topic: str, payload: str | bytes) -> NexusDevice | None:
    """Un message « homeassistant/device/<objet>/config » d'un appareil Nexus System, sinon None."""
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if not payload:
        return None
    try:
        doc = json.loads(payload)
    except ValueError:
        return None
    if not isinstance(doc, dict):
        return None
    dev = doc.get("dev") or doc.get("device")
    if not isinstance(dev, dict) or (dev.get("mf") or dev.get("manufacturer")) != MANUFACTURER:
        return None
    ids = dev.get("ids") or dev.get("identifiers")
    if isinstance(ids, str):
        ids = [ids]
    if not ids or not isinstance(ids[0], str):
        return None
    base = ""
    for item in doc.get("avty") or doc.get("availability") or []:
        t = item.get("t") or item.get("topic") if isinstance(item, dict) else None
        if isinstance(t, str) and t.endswith("/lwt"):
            base = t[: -len("/lwt")]
            break
    if not base:
        return None  # sans sujet de base, rien à commander ni à surveiller
    parts = topic.split("/")
    group = parts[2] if len(parts) == 4 else ""
    prefix = ids[0] + "_"
    return NexusDevice(
        device_id=ids[0],
        name=str(dev.get("name") or ids[0]),
        model=str(dev.get("mdl") or dev.get("model") or ""),
        serial=str(dev.get("sn") or dev.get("serial_number") or ""),
        firmware=str(dev.get("sw") or dev.get("sw_version") or ""),
        base_topic=base,
        groups={group[len(prefix):] if group.startswith(prefix) else group} if group else set(),
    )
