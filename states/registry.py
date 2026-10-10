"""Profile registry — resolves state codes and IINs to JurisdictionProfiles."""

from typing import Dict, List, Optional

from .base import JurisdictionProfile
from .us_states import DRAFT_PROFILES
from .wa import PROFILE as WA_PROFILE
from .mi import PROFILE as MI_PROFILE

# Researched profiles override draft entries.
_REGISTRY: Dict[str, JurisdictionProfile] = dict(DRAFT_PROFILES)
_REGISTRY["WA"] = WA_PROFILE
_REGISTRY["MI"] = MI_PROFILE

_IIN_INDEX: Dict[str, str] = {p.iin: p.state for p in _REGISTRY.values()}


def register(profile: JurisdictionProfile) -> None:
    """Register/override a profile (used when a state graduates from draft)."""
    _REGISTRY[profile.state.upper()] = profile
    _IIN_INDEX[profile.iin] = profile.state.upper()


def get_profile(state: str) -> JurisdictionProfile:
    key = (state or "").strip().upper()
    if key not in _REGISTRY:
        raise ValueError(
            f"Unknown jurisdiction '{state}'. Use /api/states or --list-states "
            f"for the supported list."
        )
    return _REGISTRY[key]


def try_get_profile(state: str) -> Optional[JurisdictionProfile]:
    try:
        return get_profile(state)
    except ValueError:
        return None


def iin_to_state(iin: str) -> Optional[str]:
    """Map a 6-digit jurisdiction/IIN code back to a state postal code."""
    return _IIN_INDEX.get((iin or "").strip())


def state_name(state: str) -> str:
    p = try_get_profile(state)
    return p.name if p else state


def list_states() -> List[Dict]:
    """Summary of every registered jurisdiction (for UI dropdown / CLI)."""
    out = []
    for st in sorted(_REGISTRY):
        p = _REGISTRY[st]
        out.append({
            "state": p.state,
            "name": p.name,
            "iin": p.iin,
            "aamva_version": p.aamva_version,
            "subfiles": [sf.type_id for sf in p.subfiles],
            "barcode": {
                "columns": p.barcode.columns,
                "rows": p.barcode.rows,
                "security_level": p.barcode.security_level,
                "flip_horizontal": p.barcode.flip_horizontal,
            },
            "status": "researched" if st in ("WA", "MI") else "draft",
            "notes": p.notes,
        })
    return out
