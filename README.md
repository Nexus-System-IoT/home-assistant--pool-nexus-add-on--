# Nexus System Local

Vos appareils Nexus System (Pool Nexus, et les produits suivants) dans Home Assistant, **sur votre
réseau local**, sans passer par le cloud Nexus System.

[English version](README-EN.md)

## Comment ça marche

Chaque appareil Nexus System publie lui-même, sur **votre** serveur MQTT (broker), la découverte
Home Assistant : Home Assistant crée seul l'appareil et toutes ses entités (mesures, état, alertes,
réglages, commandes), dans la langue de l'appareil, par l'intégration **MQTT**. Rien à déclarer à
la main, et une nouvelle version du firmware apporte ses nouvelles entités d'elle-même.

L'intégration **Nexus System Local** reconnaît ces appareils, quel que soit le produit, et ajoute :

| Ajout | À quoi ça sert |
|---|---|
| **Liaison locale** (capteur binaire, une par appareil) | En ligne / hors ligne sur le broker, pour vos automatisations et alertes. |
| **Action « Envoyer à un appareil Nexus »** (`nexus_system_local.send`) | Envoyer un réglage ou une commande ; l'appareil applique les mêmes contrôles que l'application. |
| **Évènement `nexus_system_local_result`** | La réponse de l'appareil à chaque envoi. |
| **Réparation** | Prévient si la découverte MQTT est désactivée (les entités n'apparaîtraient pas). |
| **Diagnostic** | La liste des appareils vus, leur firmware et leur sujet MQTT. |

## Installation

1. **Broker MQTT** : installez le module complémentaire **Mosquitto**, créez un utilisateur dédié
   à vos appareils et activez l'écoute **TLS** (port 8883) avec votre certificat.
2. **Intégration MQTT** de Home Assistant, découverte activée (c'est le réglage par défaut).
3. **Dans l'application Nexus System** : ouvrez l'appareil, *Configuration locale* (ou la mise en
   service Bluetooth), réglez le broker (adresse, port, identifiant, mot de passe, TLS).
   L'appareil apparaît dans Home Assistant en quelques secondes.
4. **Nexus System Local** : HACS › Dépôts personnalisés › ce dépôt (catégorie *Intégration*),
   installez, redémarrez Home Assistant, puis Paramètres › Appareils et services › Ajouter ›
   *Nexus System Local*. L'assistant montre les appareils trouvés sur le broker.

Une seule installation suit tous les appareils Nexus System du broker.

## Exemples

Allumer l'éclairage d'un Pool Nexus :

```yaml
action: nexus_system_local.send
data:
  device_id: <votre appareil>
  data:
    outputs:
      lights: true
```

Être prévenu quand un appareil perd sa liaison locale :

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.pool_nexus_pn0000001_liaison_locale
    to: "off"
    for: "00:05:00"
actions:
  - action: notify.notify
    data:
      message: "Le Pool Nexus ne répond plus sur le réseau local."
```

Les clés acceptées par chaque appareil, les entités créées et la sécurité (broker non chiffré :
seuls les éclairages restent commandables) sont décrites dans la documentation « Mode local, MQTT
local et Home Assistant » de Nexus System.

## Depuis l'ancienne intégration « PoolNexus »

L'ancienne intégration (`poolnexus`) écoutait des sujets `poolnexus/<série>/…` que les appareils ne
publient plus. Supprimez-la (Paramètres › Appareils et services › PoolNexus › Supprimer), puis
suivez l'installation ci-dessus.

## Développement

```bash
python3 tests/test_discovery.py                          # lecture des messages, sans Home Assistant
pip install pytest-homeassistant-custom-component && pytest   # l'intégration dans un Home Assistant de test
```
