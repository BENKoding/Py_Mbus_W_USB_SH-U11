# PC Interface for USB↔RS485/RS422 (SH‑U11)

Draft implementation scaffold aligned with the technical specification.

## Quickstart

- Prerequisites: Python 3.11 on Windows 10/11.
- Create a virtual environment and install requirements:

```
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

- Run the UI (Streamlit):

```
streamlit run app.py
```

## Packaging (PyInstaller)

Example command (to be refined as the app grows):

```
pyinstaller --noconfirm --onefile \
  --name RS485_UI \
  --add-data "ui/pages;ui/pages" \
  --add-data "profiles;profiles" \
  --add-data "config;config" \
  app.py
```

## Structure

- `core/` — Serial and Modbus helpers
- `profiles/` — YAML profiles + schema and loader
- `ui/pages/` — Streamlit multipage UI
- `storage/` — SQLite helpers and exports
- `config/` — Defaults and environment sample
- `logs/` — App logs (created at runtime)

## Notes

- Default role is Read‑Only; write actions are gated.
- The Modbus scan is conservative (try FC03 at addr 0); can be extended.
- SQLite integration and 5 Hz acquisition thread are stubbed for iteration.

