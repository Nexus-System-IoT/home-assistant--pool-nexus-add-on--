"""Constantes de l'intégration Nexus System Local."""

DOMAIN = "nexus_system_local"

# Découverte « par appareil » publiée par les appareils Nexus System (Home Assistant 2024.11+).
DISCOVERY_TOPIC = "homeassistant/device/+/config"
MANUFACTURER = "Nexus System"

# Sous le sujet de base de l'appareil (« <Modèle>-<série> ») : disponibilité, commandes, réponses.
LWT_SUFFIX = "/lwt"
SET_SUFFIX = "/local/set"
RESULT_SUFFIX = "/local/result"

SIGNAL_NEW_DEVICE = f"{DOMAIN}_new_device"
SIGNAL_DEVICE_UPDATE = f"{DOMAIN}_update_{{}}"

EVENT_RESULT = f"{DOMAIN}_result"
SERVICE_SEND = "send"
SCAN_SECONDS = 3
