"""
Model registry helpers for NEXUS GRID controller checkpoints.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch


CORE_DIR = Path(__file__).resolve().parent
NEXUSGRID_DIR = CORE_DIR.parent
MODELS_DIR = NEXUSGRID_DIR / "models"
LEGACY_WEIGHTS_PATH = CORE_DIR / "dqn_weights.pt"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "model"


def schema_fingerprint(schema: Optional[Dict[str, Any]]) -> str:
    if not schema:
        return "default"
    payload = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def resolve_model_id(
    schema: Optional[Dict[str, Any]] = None,
    preset_id: Optional[str] = None,
) -> str:
    if preset_id:
        return f"preset-{_slugify(preset_id)}"
    if schema:
        district = _slugify(str(schema.get("district_name", "district")))
        return f"schema-{district}-{schema_fingerprint(schema)}"
    return "default-demo"


def model_dir(model_id: str) -> Path:
    return MODELS_DIR / _slugify(model_id)


def checkpoint_path(model_id: str) -> Path:
    return model_dir(model_id) / "checkpoint.pt"


def metadata_path(model_id: str) -> Path:
    return model_dir(model_id) / "metadata.json"


def ensure_model_dir(model_id: str) -> Path:
    path = model_dir(model_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_metadata(
    model_id: str,
    n_buildings: int,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = {
        "model_id": model_id,
        "n_buildings": n_buildings,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        metadata.update(extra)
    return metadata


def list_models() -> List[Dict[str, Any]]:
    if not MODELS_DIR.exists():
        return []

    models: List[Dict[str, Any]] = []
    for path in sorted(MODELS_DIR.iterdir()):
        if not path.is_dir():
            continue

        meta_file = path / "metadata.json"
        checkpoint_file = path / "checkpoint.pt"
        if not meta_file.exists():
            continue

        try:
            metadata = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        metadata["has_checkpoint"] = checkpoint_file.exists()
        metadata["checkpoint_path"] = str(checkpoint_file)
        models.append(metadata)

    return models


def get_model(model_id: str) -> Optional[Dict[str, Any]]:
    target_dir = model_dir(model_id)
    meta_file = target_dir / "metadata.json"
    checkpoint_file = target_dir / "checkpoint.pt"

    if not meta_file.exists():
        return None

    try:
        metadata = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception:
        return None

    metadata["has_checkpoint"] = checkpoint_file.exists()
    metadata["checkpoint_path"] = str(checkpoint_file)

    if checkpoint_file.exists():
        try:
            checkpoint = torch.load(checkpoint_file, map_location="cpu", weights_only=True)
        except TypeError:
            checkpoint = torch.load(checkpoint_file, map_location="cpu")

        reward_history = checkpoint.get("reward_history", [])
        metadata["episode"] = checkpoint.get("episode", 0)
        metadata["epsilon"] = checkpoint.get("epsilon")
        metadata["reward_history_length"] = len(reward_history)
        metadata["reward_history_tail"] = reward_history[-10:]
        metadata["best_recorded_reward"] = max(reward_history) if reward_history else None
        metadata["latest_recorded_reward"] = reward_history[-1] if reward_history else None

    return metadata
