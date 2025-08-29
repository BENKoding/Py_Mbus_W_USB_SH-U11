from __future__ import annotations

import json

import streamlit as st

from profiles.loader import load_profiles


st.title("Profils d'appareils")

profiles = load_profiles()

if not profiles:
    st.info("Aucun profil trouvé dans `profiles/`. Un exemple est disponible.")
else:
    st.success(f"{len(profiles)} profil(s) chargé(s)")
    for key, prof in profiles.items():
        with st.expander(key):
            st.json(json.loads(prof.model_dump_json(indent=2)))

