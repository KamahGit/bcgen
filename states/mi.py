"""Michigan — IIN 636032.

Researched from a real MI license dump (Rev 08-16-2021):
  ANSI 636032030102DL00410210ZM02510027DL...
  Two subfiles: DL and ZM, separated by carriage return; elements by LF.

MI DL order (from the sample):
  DCA, DCB, DCD, DBA, DCS, DCT, DBD, DBB, DBC, DAY, DAU, DAG, DAI, DAJ,
  DAK, DAQ, DCF, DCG, DCH, DAH, DCK, DDA

NOTE: geometry (rows/columns) for MI is not yet verified -> default config,
no horizontal flip.  ZM jurisdiction-specific subfile IS included as the
first researched example of the staged subfile rollout.
"""

from .base import BarcodeConfig, JurisdictionProfile, SubFileSpec

MI_DL_ORDER = [
    "DCA",   # class (empty in sample -> skipped when blank)
    "DCB",   # restrictions
    "DCD",   # endorsements
    "DBA",   # expiration
    "DCS",   # last name
    "DCT",   # first name (MI uses DCT for first/given on the card face order)
    "DBD",   # issue date
    "DBB",   # birth date
    "DBC",   # sex
    "DAY",   # eye color
    "DAU",   # height
    "DAG",   # street address
    "DAI",   # city
    "DAJ",   # state
    "DAK",   # zip (padded to 11)
    "DAQ",   # customer id
    "DCF",   # document discriminator
    "DCG",   # country / jurisdiction
    "DCH",   # jurisdiction code (MI-specific placement)
    "DAH",   # mailing state (emitted empty in sample)
    "DCK",   # audit information
    "DDA",   # compliance type ('F' federal in sample)
]

# ZM subfile: jurisdiction-specific.  Elements ZMA/ZMB.. carry free-form text
# supplied under data key 'zm_elements' = {"ZMA": "...", "ZMB": "..."}.
MI_ZM_SUBFILE = SubFileSpec(
    type_id="ZM",
    element_order=["ZMA", "ZMB"],
    field_map={},   # values come straight from license_data['zm_elements']
)

PROFILE = JurisdictionProfile(
    state="MI",
    name="Michigan",
    iin="636032",
    aamva_version="09",
    subfiles=[
        SubFileSpec(type_id="DL", element_order=list(MI_DL_ORDER)),
        MI_ZM_SUBFILE,
    ],
    barcode=BarcodeConfig(columns=13, rows=None, security_level=5,
                          flip_horizontal=False),
    class_values=("NONE",),
    notes=("DL order + ZM subfile taken from real MI sample; PDF417 geometry "
           "pending verification."),
)
