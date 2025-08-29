from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import yaml

from .schema import DeviceProfile


logger = logging.getLogger(__name__)


def load_profiles(dir_path: str | Path = "profiles") -> Dict[str, DeviceProfile]:
    base = Path(dir_path)
    profiles: Dict[str, DeviceProfile] = {}
    if not base.exists():
        logger.warning("Profiles directory does not exist: %s", base)
        return profiles
    for yml in base.glob("*.y*ml"):
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8"))
            prof = DeviceProfile.model_validate(data)
            key = f"{prof.meta.brand}:{prof.meta.model}"
            profiles[key] = prof
            logger.info("Loaded profile %s from %s", key, yml)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load profile %s: %s", yml, exc)
    return profiles

