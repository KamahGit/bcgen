"""
Core data model for state jurisdiction profiles.

A JurisdictionProfile captures everything that varies between states:
  * IIN / jurisdiction code (e.g. WA = 636045, MI = 636032)
  * the ordering of data elements inside the DL subfile
  * optional jurisdiction-specific subfiles (ZW, ZM, ...) — added in stages
  * PDF417 geometry (rows/columns/security level) hardcoded per state
  * whether the rendered barcode is horizontally flipped (Washington does;
    other states do not)
  * per-state field defaults / vocabularies (class, restrictions, endorsements)

Adding a new jurisdiction-specific subfile later requires only appending a
SubFileSpec to the profile's ``subfiles`` list — no core refactoring.
"""

from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Optional


# Subfiles are separated by carriage return; elements within a subfile are
# separated by line feed (see AAMVA standard and real-world MI/WA dumps).
SUBFILE_DELIMITER = "\r"
ELEMENT_DELIMITER = "\n"

# Generic default PDF417 geometry used until a state is verified.
DEFAULT_BARCODE_CONFIG = {"columns": 13, "rows": None, "security_level": 5}

# ---------------------------------------------------------------------------
# Field definitions (shared schema used by backend, API and frontend)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FieldDef:
    """Definition of one input field shown in the UI / accepted by the API."""
    key: str                    # e.g. 'last_name'
    element_id: str             # e.g. 'DCS'
    label: str                  # e.g. 'Last Name'
    required: bool = False
    example: str = ""
    description: str = ""
    uppercase: bool = True
    kind: str = "text"          # text | date | select | dropdown-bool
    options: tuple = ()         # for select fields: ((value,label),...)
    max_length: int = 0
    auto_default: Optional[str] = None   # default applied when omitted


# Maps every known AAMVA element id to its canonical logical field name.
ELEMENT_FIELD_MAP: Dict[str, str] = {
    "DCA": "class",
    "DCB": "restrictions",
    "DCC": "endorsements",
    "DCD": "personalized_descriptors",
    "DCE": "weight_range",
    "DAC": "first_name",
    "DAD": "middle_name",
    "DAE": "suffix",
    "DBA": "expiration_date",
    "DCS": "last_name",
    "DCT": "first_name_trunc",
    "DCU": "suffix_trunc",
    "DAQ": "customer_id",
    "DBD": "issue_date",
    "DBB": "birth_date",
    "DBC": "sex",
    "DAY": "eye_color",
    "DAZ": "hair_color",
    "DAU": "height",
    "DAW": "weight_pounds",
    "DAG": "address_street",
    "DAI": "address_city",
    "DAJ": "address_state",
    "DAK": "address_zip",
    "DAF": "mail_street",
    "DAH": "mail_state",
    "DAK": "address_zip",
    "DCF": "document_discriminator",
    "DCG": "country_id",
    "DCK": "audit_information",
    "DCL": "family_name_trunc",
    "DCM": "given_name_trunc",
    "DCN": "under_18_until",
    "DCO": "name_prefix",
    "DBN": "alias_name",
    "DCI": "place_of_birth",
    "DCJ": "inventory_control",
    "DDA": "compliance_type",
    "DDB": "card_revision_date",
    "DDC": "hazmat_expiry",
    "DDD": "limited_duration",
    "DDE": "jurisdiction_endorsement_expiration",
    "DDF": "jurisdiction_endorsement_code",
    "DDG": "jurisdiction_restriction_code",
    "DDH": "under_18_until",
    "DDI": "under_19_until",
    "DDJ": "under_21_until",
    "DDK": "organ_donor",
    "DDL": "veteran",
}

# Backwards-compatible alias used by older code paths.
GENERIC_DL_ORDER: List[str] = [
    "DCA", "DCB", "DCC", "DCD", "DBA", "DCS", "DCT", "DCU", "DAQ", "DBD",
    "DBB", "DBC", "DAY", "DAZ", "DAU", "DAW", "DAG", "DAI", "DAJ", "DAK",
    "DCF", "DCG", "DCL", "DCM", "DDA", "DDB", "DDE", "DDF", "DDG",
]


# ---------------------------------------------------------------------------
# Subfile specification
# ---------------------------------------------------------------------------

@dataclass
class SubFileSpec:
    """One subfile inside the barcode body (DL, ID, ZW, ZM, ...).

    ``element_order`` lists element IDs in the exact order this jurisdiction
    emits them.  Elements whose value is None/empty are skipped; unknown keys
    in the license data resolve through ELEMENT_FIELD_MAP.
    """
    type_id: str                              # 'DL', 'ZM', 'ZW', ...
    element_order: List[str] = dc_field(default_factory=list)
    # For non-DL subfiles: mapping of element id -> callable(data)->value or
    # plain string template.  Kept simple: element id -> data key.
    field_map: Dict[str, str] = dc_field(default_factory=dict)


# ---------------------------------------------------------------------------
# Barcode geometry
# ---------------------------------------------------------------------------

@dataclass
class BarcodeConfig:
    """Hardcoded PDF417 geometry for a jurisdiction."""
    columns: int = DEFAULT_BARCODE_CONFIG["columns"]
    rows: Optional[int] = None            # None = let encoder decide
    security_level: int = DEFAULT_BARCODE_CONFIG["security_level"]
    flip_horizontal: bool = False         # True only for Washington today
    image_width: int = 3430               # render target px
    image_height: int = 603


# ---------------------------------------------------------------------------
# Jurisdiction profile
# ---------------------------------------------------------------------------

@dataclass
class JurisdictionProfile:
    """Everything state-specific about a driver-license barcode."""
    state: str                       # two-letter postal code
    name: str                        # e.g. 'Washington'
    iin: str                         # 6-digit issuer identification number
    aamva_version: str = "09"
    jurisdiction_version: str = "00"
    subfiles: List[SubFileSpec] = dc_field(default_factory=list)
    barcode: BarcodeConfig = dc_field(default_factory=BarcodeConfig)
    # Per-state vocabularies / defaults (may override generic ones)
    class_values: tuple = ("NONE",)
    restriction_values: tuple = ("NONE",)
    endorsement_values: tuple = ("NONE",)
    compliance_values: tuple = (("N", "Non-compliant"),
                                ("R", "REAL ID compliant"),
                                ("E", "Enhanced compliant"),
                                ("B", "Both REAL ID and Enhanced"))
    card_revision_default: Optional[str] = None    # e.g. WA '2019-11-12'
    mandatory_fields: tuple = ()                   # extra required field keys
    optional_fields: tuple = ()                    # extra supported field keys
    notes: str = ""

    # -- convenience ------------------------------------------------------
    @property
    def dl(self) -> SubFileSpec:
        return self.subfiles[0]

    def all_element_ids(self) -> List[str]:
        ids: List[str] = []
        for sf in self.subfiles:
            ids.extend(sf.element_order)
        return ids


def build_default_profile(state: str, name: str, iin: str,
                          **overrides) -> JurisdictionProfile:
    """Create a profile with the generic DL ordering; extra subfiles can be
    appended later without touching generator logic."""
    kwargs = dict(
        state=state,
        name=name,
        iin=iin,
        subfiles=[SubFileSpec(type_id="DL", element_order=list(GENERIC_DL_ORDER))],
    )
    kwargs.update(overrides)
    return JurisdictionProfile(**kwargs)
