from __future__ import annotations

import logging

import streamlit as st

from core.serial_comm import SerialParams, list_serial_ports, open_serial, test_loopback
from core.modbus_client import ModbusParams, ModbusRTUClient


logger = logging.getLogger(__name__)


st.title("Connexion")

# Role selection
role = st.selectbox("Rôle", ["RO", "OP", "ADMIN"], index=["RO", "OP", "ADMIN"].index(st.session_state.get("role", "RO")))
st.session_state.role = role

ports = list_serial_ports()
port_labels = [p["device"] + (f" — {p['description']}" if p.get("description") else "") for p in ports]

if not ports:
    st.warning("Aucun port série détecté. Branchez l'adaptateur USB↔RS485.")
else:
    idx_default = 0
    sel = st.selectbox("Port COM", options=list(range(len(ports))), format_func=lambda i: port_labels[i], index=idx_default)
    selected_port = ports[sel]["device"]

    cols = st.columns(5)
    with cols[0]:
        baud = st.selectbox("Baud", [9600, 19200, 38400, 57600, 115200], index=0)
    with cols[1]:
        parity = st.selectbox("Parité", ["N", "E", "O"], index=0)
    with cols[2]:
        stopbits = st.selectbox("Stop", [1, 2], index=0)
    with cols[3]:
        bytesize = st.selectbox("Bits", [8, 7], index=0)
    with cols[4]:
        timeout = st.number_input("Timeout (s)", min_value=0.05, max_value=5.0, value=0.3, step=0.05)

    sp = SerialParams(
        port=selected_port,
        baudrate=baud,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize,
        timeout_s=float(timeout),
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Test bouclage (optionnel)"):
            try:
                with open_serial(sp) as ser:
                    ok = test_loopback(ser)
                st.success("Bouclage OK" if ok else "Bouclage NON OK")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Erreur: {exc}")

    # Modbus connection
    mp = ModbusParams(
        port=sp.port,
        baudrate=sp.baudrate,
        parity=sp.parity,
        stopbits=sp.stopbits,
        bytesize=sp.bytesize,
        timeout=sp.timeout_s,
    )

    def ensure_client() -> ModbusRTUClient:
        if "mb_client" not in st.session_state:
            st.session_state.mb_client = ModbusRTUClient()
        return st.session_state.mb_client

    with c2:
        if st.button("Se connecter"):
            cli = ensure_client()
            if cli.connect(mp):
                st.session_state.connection = {"connected": True, "port": sp.port}
                st.success(f"Connecté sur {sp.port}")
            else:
                st.session_state.connection = {"connected": False, "port": None}
                err = getattr(cli, "last_error", None)
                if err:
                    st.error(f"Échec de connexion: {err}")
                else:
                    st.error("Échec de connexion")
    with c3:
        if st.button("Se déconnecter"):
            cli = ensure_client()
            cli.close()
            st.session_state.connection = {"connected": False, "port": None}
            st.info("Déconnecté")

st.caption("Astuce: pour RS485 half‑duplex, vérifier la terminaison 120 Ω côté bus.")
