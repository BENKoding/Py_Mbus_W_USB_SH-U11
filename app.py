from __future__ import annotations

import json
import logging
from pathlib import Path

import streamlit as st
import yaml

from logging_setup import setup_logging


def load_defaults() -> dict:
    cfg_path = Path("config/defaults.yaml")
    if cfg_path.exists():
        return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    return {}


defaults = load_defaults()
log_cfg = defaults.get("logging", {})
setup_logging(
    level=log_cfg.get("level", "INFO"),
    log_path=log_cfg.get("path", "logs/app.log"),
    max_bytes=log_cfg.get("max_bytes", 1_048_576),
    backup_count=log_cfg.get("backup_count", 3),
)
logger = logging.getLogger(__name__)


st.set_page_config(page_title="Modbus RTU UI", page_icon="🔌", layout="wide")

# Session state defaults
if "role" not in st.session_state:
    st.session_state.role = "RO"  # RO / OP / ADMIN
if "connection" not in st.session_state:
    st.session_state.connection = {"connected": False, "port": None}

st.title("Interface Modbus RTU (USB↔RS485)")
st.caption("MVP — Connexion, Scan, Lecture de base")

st.subheader("État")
cols = st.columns(3)
with cols[0]:
    st.metric("Rôle", st.session_state.role)
with cols[1]:
    st.metric("Connexion", "OK" if st.session_state.connection.get("connected") else "Hors ligne")
with cols[2]:
    st.metric("Port", st.session_state.connection.get("port") or "—")

st.divider()

st.markdown("""
Pages principales:
- Connexion — sélectionner le port série et tester.
- Scan réseau — détecter les esclaves Modbus (1…247).
- Appareil — lecture/écriture avec profils YAML.
- Graphes — visualisation (à venir).
- Console — trames brutes (à venir).
- Journal & Export — logs et exports (à venir).
- Profils — gestion des profils d'appareils.
""")

with st.expander("Configuration chargée"):
    st.code(json.dumps(defaults, indent=2, ensure_ascii=False))

st.info("Mode Lecture seule par défaut. Passez en rôle Opérateur/Admin dans la page Connexion si nécessaire.")

