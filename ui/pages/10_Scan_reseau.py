from __future__ import annotations

import time

import streamlit as st


st.title("Scan réseau Modbus")

if not st.session_state.get("connection", {}).get("connected"):
    st.warning("Non connecté. Allez à la page Connexion.")
    st.stop()

start_id = st.number_input("Adresse début", min_value=1, max_value=247, value=1, step=1)
end_id = st.number_input("Adresse fin", min_value=1, max_value=247, value=10, step=1)
probe_addr = st.number_input("Adresse reg. sonde (FC03)", min_value=0, max_value=65535, value=0, step=1)
count = st.number_input("Nb registres", min_value=1, max_value=4, value=1, step=1)

place = st.empty()
result = st.empty()

if st.button("Scanner"):
    cli = st.session_state.get("mb_client")
    ids = list(range(int(start_id), int(end_id) + 1))
    found: list[int] = []
    prog = st.progress(0.0, text="Scan en cours…")
    for i, uid in enumerate(ids, start=1):
        ok = False
        try:
            regs = cli.read_holding(unit=uid, address=int(probe_addr), count=int(count))
            ok = regs is not None
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            found.append(uid)
            result.info(f"Présent: {found}")
        prog.progress(i / len(ids), text=f"Scan {i}/{len(ids)}")
        time.sleep(0.02)
    prog.empty()
    if found:
        st.success(f"Trouvés: {found}")
    else:
        st.info("Aucun esclave détecté sur l'intervalle donné.")

