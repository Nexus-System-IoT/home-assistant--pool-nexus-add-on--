<p align="center">
  <img src="custom_components/nexus_system_local/brand/icon@2x.png" width="140" alt="Nexus System">
</p>

<h1 align="center">Nexus System Local — intégration Home Assistant</h1>

<p align="center">
  Vos appareils <b>Nexus System</b> (Pool Nexus, et les produits suivants) dans Home Assistant,
  <b>sur votre réseau local</b>, sans passer par le cloud.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS Custom"></a>
  <img src="https://img.shields.io/github/v/release/Nexus-System-IoT/home-assistant--pool-nexus-add-on--?style=for-the-badge" alt="Release">
  <img src="https://img.shields.io/github/downloads/Nexus-System-IoT/home-assistant--pool-nexus-add-on--/total?style=for-the-badge&label=installs&color=success" alt="Installs">
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.11%2B-049CDB?style=for-the-badge&logo=home-assistant&logoColor=white" alt="HA">
</p>

[English version](README-EN.md)

---

## ✨ Fonctionnalités

Chaque appareil Nexus System publie **lui-même** sa découverte Home Assistant sur votre broker
MQTT : Home Assistant crée l'appareil et toutes ses entités, dans la langue de l'appareil, sans
rien déclarer à la main. Une mise à jour du firmware apporte ses nouvelles entités d'elle-même.

Pour un **Pool Nexus**, un seul appareil « Pool Nexus &lt;série&gt; » avec :

| Groupe | Entités | Type |
| --- | --- | --- |
| Mesures | pH, redox (mV), température de l'eau, pression 1 et 2 (si posés), mV bruts des sondes | `sensor` |
| Eau et produits | niveau d'eau bas, bidons pH- et chlore (niveau et alerte), débit de filtration, protection antigel, remplissage en cours | `sensor`, `binary_sensor` |
| Dosage | pompes doseuses pH- et chlore, quantités injectées sur 24 h, dernière dose, temps de marche | `sensor`, `binary_sensor` |
| Sondes | état, pente, décalage, dernier étalonnage, sonde non étalonnée | `sensor`, `binary_sensor` |
| Alertes | alertes en cours, puis une entité par alerte (sonde, débit, bidon, dosage bloqué, certificat…) | `sensor`, `binary_sensor` |
| Commandes | filtration, éclairage 1, éclairage 2 ; mode de filtration ; régulation pH et chlore, remplissage automatique | `switch`, `select` |
| Réglages | consignes pH et redox, cadence des mesures locales, pompe à chaleur branchée, pompe à vitesse variable | `number`, `switch` |
| Pauses | suspendre / reprendre la régulation ou la filtration 24 h | `button` |
| Informations | hivernage, volume du bassin, capteurs de pression, pression minimale, filtration prévue aujourd'hui | `sensor` |
| Diagnostic | micrologiciel (mise à jour), Wi-Fi, liaison réseau, adresse IP, durée de fonctionnement, cause du dernier redémarrage, cloud, Matter, dernière commande | `update`, `sensor`, `binary_sensor` |

L'intégration **Nexus System Local** reconnaît ces appareils, quel que soit le produit, et ajoute :

| Ajout | Type | Détail |
| --- | --- | --- |
| Liaison locale | `binary_sensor` (connectivité) | en ligne / hors ligne sur le broker, une par appareil |
| Envoyer à un appareil Nexus | action `nexus_system_local.send` | réglage ou commande ; l'appareil applique les mêmes contrôles que l'app |
| Réponse de l'appareil | évènement `nexus_system_local_result` | le résultat de chaque envoi |
| Découverte MQTT désactivée | réparation | prévient : sans elle, aucune entité n'apparaît |
| Diagnostic | téléchargeable | appareils vus, firmware, sujet MQTT |

> 🔒 Rien ne passe par le cloud Nexus System. Avec un broker **non chiffré**, l'appareil n'accepte
> que les éclairages ; le reste est en lecture seule.

---

## 📦 Installation

### 1. Broker MQTT

1. Installez le module complémentaire **Mosquitto broker**.
2. Créez un utilisateur dédié à vos appareils et activez l'écoute **TLS** (port 8883) avec votre certificat.
3. Ajoutez l'intégration **MQTT** de Home Assistant (découverte activée, c'est le réglage par défaut).

### 2. L'appareil

Dans l'application **Nexus System** : ouvrez l'appareil › **Configuration locale** (ou la mise en
service Bluetooth) › réglez le broker : adresse, port, identifiant, mot de passe, TLS. L'appareil
apparaît dans Home Assistant en quelques secondes.

### 3. Nexus System Local via HACS (recommandé)

[![Ouvrir dans HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Nexus-System-IoT&repository=home-assistant--pool-nexus-add-on--&category=integration)

1. Cliquez le bouton ci-dessus **ou** : HACS › menu ⋮ (en haut à droite) › **Dépôts personnalisés**
2. URL : `https://github.com/Nexus-System-IoT/home-assistant--pool-nexus-add-on--` — catégorie : **Intégration**
3. Ouvrez **Nexus System Local** dans la liste › **Télécharger**
4. **Redémarrez** Home Assistant

### Manuelle

Copiez le dossier `custom_components/nexus_system_local/` dans le dossier
`config/custom_components/` de votre Home Assistant, puis redémarrez.

---

## ⚙️ Configuration

[![Ajouter l'intégration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=nexus_system_local)

*Paramètres › Appareils et services › **Ajouter une intégration** › « Nexus System Local »*.
L'assistant vérifie MQTT et affiche les appareils trouvés sur le broker. Une seule installation
suit tous les appareils Nexus System du broker, y compris ceux ajoutés plus tard.

---

## 🤖 Exemples

### Allumer l'éclairage

```yaml
action: nexus_system_local.send
data:
  device_id: <votre appareil>
  data:
    outputs:
      lights: true
```

### Être prévenu quand le Pool Nexus ne répond plus

```yaml
automation:
  - alias: Pool Nexus - liaison perdue
    triggers:
      - trigger: state
        entity_id: binary_sensor.pool_nexus_pn0000001_liaison_locale
        to: "off"
        for: { minutes: 5 }
    actions:
      - action: notify.notify
        data:
          title: Pool Nexus
          message: "Le Pool Nexus ne répond plus sur le réseau local."
```

### Suivre la réponse de l'appareil

```yaml
automation:
  - alias: Nexus - réglage refusé
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
          message: "Réglage refusé : {{ trigger.event.data.result.error }}"
```

> Remplacez `pn0000001` par le numéro de série de votre appareil (visible dans l'entity-id généré).

Les clés acceptées par chaque appareil, toutes les entités et les sujets MQTT sont détaillés dans
la documentation [MQTT local et domotique](https://developer.nexus-system.fr/docs?page=MQTT%20local%20et%20domotique)
et le [guide Home Assistant](https://developer.nexus-system.fr/integrations/home-assistant).

---

## 🔁 Depuis l'ancienne intégration « PoolNexus »

L'ancienne intégration (`poolnexus`) écoutait des sujets `poolnexus/<série>/…` que les appareils
ne publient plus. Supprimez-la (Paramètres › Appareils et services › PoolNexus › Supprimer), puis
suivez l'installation ci-dessus.

---

## 📊 Adoption

- 🔢 Badge **installs** (en haut) : téléchargements cumulés de l'asset `.zip` comptés par GitHub (installations et mises à jour).
- 📈 **HA Analytics** (installations actives) : [analytics.home-assistant.io/custom_integrations](https://analytics.home-assistant.io/custom_integrations/) › domaine `nexus_system_local`, mis à jour chaque semaine.

<p align="center">
  <a href="https://star-history.com/#Nexus-System-IoT/home-assistant--pool-nexus-add-on--&Date">
    <img src="https://api.star-history.com/svg?repos=Nexus-System-IoT/home-assistant--pool-nexus-add-on--&type=Date" width="600" alt="Star History Chart">
  </a>
</p>

---

## 🤝 Contribuer

- 🐛 **Bug** : ouvrez une [issue](https://github.com/Nexus-System-IoT/home-assistant--pool-nexus-add-on--/issues) avec votre version de Home Assistant, celle du firmware et les journaux (`custom_components.nexus_system_local`) ; le diagnostic de l'intégration aide beaucoup.
- 💡 **Idée** : ouvrez une issue pour en discuter avant de coder.
- 🔧 **Pull request** : forkez, créez une branche, ouvrez une PR vers `main`.

### Développement

```bash
python3 tests/test_discovery.py                                 # lecture des messages, sans Home Assistant
pip install pytest-homeassistant-custom-component && pytest     # l'intégration dans un Home Assistant de test
```

### Publier une version

Augmentez `version` dans `manifest.json`, puis poussez le tag `v<version>` : la release GitHub et
l'asset `nexus_system_local.zip` (installé par HACS) sont créés automatiquement.
