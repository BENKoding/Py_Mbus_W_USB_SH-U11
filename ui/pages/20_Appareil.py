from __future__ import annotations

import struct
from typing import Dict, Optional

import streamlit as st

from core.modbus_client import ModbusRTUClient
from profiles.loader import load_profiles
from profiles.schema import Access, DeviceProfile, RegisterDef, RegType, Endianness


st.title("Vue Appareil")

if not st.session_state.get("connection", {}).get("connected"):
    st.warning("Non connecté. Allez à la page Connexion.")
    st.stop()

cli: ModbusRTUClient = st.session_state.get("mb_client")
profiles: Dict[str, DeviceProfile] = load_profiles()

if not profiles:
    st.info("Aucun profil chargé (dossier 'profiles/'). Un exemple est fourni: profiles/example_device.yaml")

unit_id = st.number_input("Adresse esclave (unit id)", min_value=1, max_value=247, value=1, step=1)

key = st.selectbox("Profil", options=["(aucun)"] + list(profiles.keys()))
profile: Optional[DeviceProfile] = profiles.get(key) if key != "(aucun)" else None


def decode_value(reg: RegisterDef, regs: list[int]) -> Optional[float]:
    try:
        if reg.type in (RegType.u16, RegType.i16):
            v = regs[0] & 0xFFFF
            if reg.type == RegType.i16 and v >= 0x8000:
                v -= 0x10000
            return float(v) * float(reg.scale)
        # 32-bit types
        w0, w1 = regs[0] & 0xFFFF, regs[1] & 0xFFFF
        if reg.endianness == Endianness.le:
            w0, w1 = w1, w0
        raw = (w0 << 16) | w1
        if reg.type == RegType.u32:
            return float(raw) * float(reg.scale)
        if reg.type == RegType.i32:
            if raw & 0x80000000:
                raw -= 0x100000000
            return float(raw) * float(reg.scale)
        if reg.type == RegType.f32:
            b = w0.to_bytes(2, "big") + w1.to_bytes(2, "big")
            f = struct.unpack(">f", b)[0]
            return float(f) * float(reg.scale)
    except Exception:  # noqa: BLE001
        return None
    return None


def encode_u16(value: float, reg: RegisterDef) -> int:
    # Very basic encoder for u16/i16 only (MVP)
    scaled = int(round(float(value) / float(reg.scale or 1.0)))
    if reg.type == RegType.i16:
        if scaled < 0:
            scaled = (scaled + 0x10000) & 0xFFFF
    return scaled & 0xFFFF


if profile:
    st.subheader(f"Profil: {key}")
    for r in profile.registers:
        cols = st.columns([2, 1, 2, 2, 2])
        cols[0].markdown(f"**{r.name}**\n`addr={r.address}` · `FC{r.function}` · `{r.type}` {r.unit or ''}")
        val_slot = cols[1].empty()
        read_btn = cols[2].button("Lire", key=f"read_{r.name}_{r.address}")
        write_col = cols[3]
        status_col = cols[4]

        if read_btn:
            if r.function == 4:
                regs = cli.read_input(unit=int(unit_id), address=r.address, count=r.words)
            else:
                regs = cli.read_holding(unit=int(unit_id), address=r.address, count=r.words)
            if regs is None:
                status_col.error("Erreur lecture")
            else:
                v = decode_value(r, regs)
                if v is None:
                    status_col.warning(f"Regs: {regs}")
                else:
                    val_slot.markdown(f"**{v}** {r.unit or ''}")

        # Write (MVP: only u16/i16 via FC06)
        can_write = (st.session_state.get("role", "RO") in ("OP", "ADMIN")) and (r.access == Access.RW)
        if can_write and r.type in (RegType.u16, RegType.i16) and r.function == 3:
            wval = write_col.number_input(
                f"Valeur ({r.unit or ''})",
                value=float(r.minimum) if r.minimum is not None else 0.0,
                key=f"val_{r.name}_{r.address}",
            )
            if write_col.button("Écrire", key=f"write_{r.name}_{r.address}"):
                # Guardrails: range check
                if r.minimum is not None and wval < r.minimum:
                    status_col.error("Sous la plage min")
                elif r.maximum is not None and wval > r.maximum:
                    status_col.error("Au‑delà de la plage max")
                else:
                    raw = encode_u16(wval, r)
                    ok = cli.write_single_register(unit=int(unit_id), address=r.address, value=raw)
                    status_col.success("Écrit") if ok else status_col.error("Échec écriture")
        else:
            write_col.caption("Lecture seule ou non supporté (MVP)")
