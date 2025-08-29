# Cahier des charges — Interface PC pour module USB↔RS485/RS422 (SH‑U11)

> **Statut** : Ébauche à compléter avec les réponses aux questions.

## 1) Contexte & objectifs

* **Contexte** : Pilotage et supervision d’appareils RS485 (ex. MFC Sensirion SFC5xxx) via convertisseur USB↔RS485/RS422 DSD TECH SH‑U11.
* **Objectifs** :

  * Découvrir les appareils présents sur le bus.
  * Lire/écrire des registres (Modbus RTU ou trames propriétaires).
  * Visualiser, historiser et exporter les données.
  * Sécuriser les opérations d’écriture.

## 2) Périmètre

* **Inclus** : PC Windows (Linux/macOS à confirmer), gestion du port COM, scan d’adresses, lecture/écriture registres, UI graphique, logs, export.
* **Exclus / Hors périmètre** : Drivers matériels du SH‑U11 (gérés par OS), développement firmware des esclaves, supervision cloud (à confirmer).

## 3) Hypothèses & contraintes

* Bus **RS485 half‑duplex**, terminaison 120 Ω, polarisation selon installation.
* Adapter gère l’auto‑direction (DE/RE). À confirmer.
* Débits typiques 9 600–115 200 bauds. Parité N/E/O, stop 1–2.

## Synthèse des décisions (verrouillées)

* **OS cibles :** Windows 10/11 uniquement.
* **Distribution :** Exécutable unique via **PyInstaller**.
* **Framework UI :** **Streamlit** (web local).
* **Écrans retenus :** Connexion, Scan réseau, Vue Appareil, Graphe temps réel, Console Hex & scripts, Journal/Export, Profils d’appareils.
* **Protocoles :** **Modbus RTU uniquement** (FC 01/02/03/04/05/06/15/16/23) pour la v1.
* **Décodage registres :** Types de base (u16/i16/u32/i32/f32) + endianness.
* **Scan :** Heuristique progressive (multi‑config priorisées) + balayage **1→247**.
* **Accès & sûreté :** Rôles **Lecture seule / Opérateur / Admin**.
* **Protections d’écriture :** **Validation type/unité + plages min/max**.
* **Profils d’appareils :** **YAML** (schéma validé) ; remplissage auto depuis datasheet quand possible.
* **Acquisition :** **5 Hz** par défaut.
* **Historisation :** **SQLite** avec export **CSV/XLSX**.
* **Logs :** fichier `.log` avec rotation (DEBUG/INFO/WARN/ERROR).
* **Tests :** priorité aux **tests sur bus réel** (scripts de recette) avec profils SFC5xxx.
* **Mode sûreté :** **Lecture seule par défaut**.

## 4) Exigences fonctionnelles (F)

* **F1.** Sélection/auto‑détection du port série & paramètres.
* **F2.** Scan des adresses Modbus (1–247) et/ou multi‑baud/parité.
* **F3.** Lecture registres (holding/input), coils/discrete si applicable.
* **F4.** Écriture simple/multiple (FC06/FC16) avec garde‑fous.
* **F5.** Profils d’appareils (mappage registres) **extensibles** (JSON/YAML).
* **F6.** Vue temps réel + tableaux + graphes
* **F7.** Journalisation (CSV/JSON) et export (CSV/XLSX).
* **F8.** Import/export de profils d’appareils & presets.
* **F9.** Mode **Lecture seule** / **Maintenance** / **Admin**.
* **F10.** Simulateur d’esclave (option) pour tests hors ligne.

## 5) Exigences non‑fonctionnelles (NF)

* **NF1.** OS cible : **Windows 10/11 uniquement**.
* **NF2.** Performance : **rafraîchissement 5 Hz** en lecture continue (UI Streamlit : rafraîchissement via `st_autorefresh`/timer ; acquisition asynchrone thread/queue).
* **NF3.** Robustesse : gestion timeouts, CRC, collisions, bus occupé ; backoff exponentiel sur scans.
* **NF4.** Traçabilité : logs horodatés, niveaux DEBUG/INFO/WARN/ERROR, rotation.
* **NF5.** Packaging : **exécutable PyInstaller** signé (si possible) ; exclusions antivirus documentées.
* **NF6.** Localisation : UI en français, unités configurables (SI).

## 6) Architecture logicielle (proposition)

* **Langage** : Python 3.11+
* **Libs cœur** : `pyserial`, `pymodbus` (RTU), `pydantic` (validation schéma YAML), `loguru`/`logging`.
* **UI** : **Streamlit** (`streamlit`, `plotly` pour graphes interactifs, `pandas` pour tables), `watchdog` pour profils.
* **Acquisition** : thread dédié (lectures Modbus planifiées), **queue** pour passer les échantillons à l’UI ; cadence cible 5 Hz.
* **Persistance** : **SQLite** (mesures), export **CSV/XLSX** ; profils **YAML** (répertoire `profiles/`).
* **Structure** :

  * `core/serial_comm.py` (port COM, paramètres, retries)
  * `core/modbus_client.py` (lecture/écriture, scan, exceptions)
  * `profiles/schema.py` (pydantic + validation)
  * `profiles/loader.py` (YAML, auto‑import datasheet)
  * `ui/pages/` (connexion, scan, appareil, graphes, console, export)
  * `storage/` (sqlite, exports, logs)

## 7) UX/UI

* **Écrans cibles (validés)** : Connexion · Scan réseau · Vue Appareil · Graphe temps réel · Console Hex & scripts · Journal/Export · Profils d’appareils.
* **Connexion** : sélection COM, auto‑détection (liste ports), paramètres (baud, parité, stop, timeout), test de bouclage.
* **Scan** : heuristique progressive (baud/parités les plus courants d’abord), balayage 1→247, indicateur de progression, annulation, résultats triables/exportables.
* **Appareil** : infos (modèle, adresse), table registres (editable si rôle ≥ Opérateur), filtres (RO/RW, unité, critère), presets de lecture/écriture.
* **Graphes** : sélection variables, fenêtres de temps, curseur, export.
* **Console Hex** : envoi trames brutes, presets, horodatage Rx/Tx.
* **Journal/Export** : vue des logs, exports CSV/XLSX des mesures et rapports de scan.
* **Profils** : liste, import YAML, assistant datasheet (auto/assisté/manuel), validation schéma, versioning local.

## 8) Gestion des appareils (Profils)

* Fichier **JSON/YAML** par appareil :

  * Métadonnées (marque, modèle, version protocole).
  * Registres (addr, type, mots, signed/endianness, scale, unité, RO/RW, range, critique=true/false).
  * Templates de commandes (séquences multi‑regs).

## 9) Sécurité / Sûreté / Qualité

* Rôles : Lecture seule / Opérateur / Admin.
* Confirms double clic pour registres critiques.
* Liste blanche des registres autorisés à l’écriture par rôle.
* **Dry‑run** / simulation avant écriture réelle.
* Back‑up/restore de configuration appareil (dump complet si supporté).

## 10) Logs & Export

* **Logs appli** : fichier `.log` (rotation), niveaux réglables, export du journal.
* **Historisation mesures** : base **SQLite** par projet/session, réindexation temporelle, purge configurable.
* **Exports** : CSV/XLSX pour mesures, JSON/YAML pour profils et résultats de scans.

## 11) Tests & Validation

* **Priorité** : **tests sur bus réel** (scripts de recette) avec MFC **Sensirion SFC5xxx**.
* **Compléments minimum** :

  * Unitaires : parsers YAML, mapping types/endianness, CRC/encodage Modbus, validations min/max.
  * Intégration : simulateur Modbus (esclave virtuel) pour CI locale, puis tests terrain.
* **Scénarios** : timeout, CRC error, exception Modbus, bus saturé, collisions, valeurs hors plage, rollback profil.
* **Sorties** : rapport de test, checklist recette, jeux de profils d’exemple.

## 12) Déploiement & Maintenance

* **Binaire Windows** : **PyInstaller** ; icône, version sémantique, hash.
* **Signature** (si cert dispo) et guide antivirus (faux positifs).
* **Configuration** : fichier `.env`/YAML pour paramètres par défaut.
* **Documentation** : guide utilisateur, guide intégration profils, FAQ.

## 13) Roadmap (alignée aux choix)

1. **MVP** (Streamlit) : Connexion + Scan heuristique (mono‑config de départ) + Lecture Modbus + Export CSV.
2. **Profils YAML** : schéma pydantic, table registres, **écriture sécurisée** (min/max + type/unité), rôles de base, logs.
3. **Historisation SQLite** : graphes Plotly, export XLSX, amélioration scan multi‑baud/parités.
4. **Assistant datasheet** : import Excel/CSV/YAML + pré‑mapping + validation ; mode manuel.
5. **Optimisations** : cadence 5 Hz stable, backoff, performances UI, journaux.
6. **Packaging** : PyInstaller + doc, jeu d’exemples (SFC5xxx), scripts de recette.

---

### Décisions encore à trancher

* **14.7 Q1–Q5** (import datasheet)
* Politique de signature du binaire
* Emplacement par défaut des profils & BDD
* Politique de purge des historiques
