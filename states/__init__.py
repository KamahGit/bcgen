"""
Jurisdiction profiles for all 50 US states (plus DC).

v2.0.0-alpha.1 — staged rollout:
  * Every state ships with a DL subfile; WA and MI carry researched element
    orderings, MI includes its ZM jurisdiction subfile as the worked example.
  * Adding more jurisdiction-specific subfiles (ZW, ZB*, ...) later requires
    only appending a SubFileSpec to that state's profile — no core changes.
  * Per-state PDF417 geometry (rows/columns) is hardcoded per profile.
  * The Washington-only horizontal flip is a profile flag, not encoder code.
"""

from .base import (
    BarcodeConfig,
    FieldDef,
    JurisdictionProfile,
    SubFileSpec,
    SUBFILE_DELIMITER,
    ELEMENT_DELIMITER,
    DEFAULT_BARCODE_CONFIG,
    GENERIC_DL_ORDER,
    ELEMENT_FIELD_MAP,
    build_default_profile,
)
from .registry import (
    get_profile,
    try_get_profile,
    list_states,
    register,
    iin_to_state,
    state_name,
)
from .fields import CORE_FIELDS, fields_as_dicts

__all__ = [
    "BarcodeConfig",
    "FieldDef",
    "JurisdictionProfile",
    "SubFileSpec",
    "SUBFILE_DELIMITER",
    "ELEMENT_DELIMITER",
    "DEFAULT_BARCODE_CONFIG",
    "GENERIC_DL_ORDER",
    "ELEMENT_FIELD_MAP",
    "build_default_profile",
    "get_profile",
    "try_get_profile",
    "list_states",
    "register",
    "iin_to_state",
    "state_name",
    "CORE_FIELDS",
    "fields_as_dicts",
]
