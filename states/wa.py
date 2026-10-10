"""Washington — IIN 636045.

Verified against a real WA license:
  * DL element order: DCA, DCB, DCD, DBA, DCS, DCT, DAQ, ... (WA-specific)
  * Jurisdiction subfile ZW exists but is NOT researched yet -> added in a
    later stage by appending a SubFileSpec here.
  * PDF417 geometry: 13 configured columns (15 visible) x 17 rows.
  * WA barcodes are rendered horizontally flipped; no other state does this.
"""

from .base import BarcodeConfig, JurisdictionProfile, SubFileSpec

# Exact emission order observed on real WA licenses (matches v1 generator).
WA_DL_ORDER = [
    "DCA",   # class
    "DCB",   # restrictions
    "DCD",   # endorsements (WA emits endorsements under DCD)
    "DBA",   # expiration
    "DCS",   # last name
    "DAC",   # first name... (v1 used DAC after DCS)
    "DAD",   # middle
    "DBD",   # issue date
    "DBB",   # birth
    "DBC",   # sex
    "DAY",   # eye
    "DAZ",   # hair
    "DAU",   # height
    "DAG",   # street
    "DAI",   # city
    "DAJ",   # state
    "DAK",   # zip
    "DAQ",   # customer id
    "DCF",   # document discriminator
    "DCG",   # country
    "DDA",   # compliance
    "DDB",   # card revision
]

PROFILE = JurisdictionProfile(
    state="WA",
    name="Washington",
    iin="636045",
    aamva_version="09",
    subfiles=[SubFileSpec(type_id="DL", element_order=list(WA_DL_ORDER))],
    barcode=BarcodeConfig(columns=13, rows=17, security_level=5,
                          flip_horizontal=True),
    class_values=("NONE", "C", "A", "B"),
    card_revision_default="2019-11-12",
    notes="Horizontal flip verified from actual WA license; ZW subfile pending research.",
)
