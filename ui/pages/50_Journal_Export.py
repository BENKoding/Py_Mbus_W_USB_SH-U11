from __future__ import annotations

from pathlib import Path

import streamlit as st


st.title("Journal & Export")

log_path = Path("logs/app.log")
if log_path.exists():
    st.subheader("Logs applicatifs")
    st.download_button("Télécharger le log", data=log_path.read_bytes(), file_name="app.log")
    st.text_area("Contenu", log_path.read_text(encoding="utf-8", errors="ignore"), height=300)
else:
    st.info("Pas encore de journal. Les logs apparaîtront ici.")

st.subheader("Exports mesures (à venir)")
st.caption("Exports CSV/XLSX depuis SQLite seront ajoutés prochainement.")

