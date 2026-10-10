"""Shared AAMVA field schema (single source of truth for backend + frontend)."""

from .base import FieldDef

SEX_OPTIONS = (("M", "Male"), ("F", "Female"), ("X", "Non-binary/Unspecified"))

EYE_COLOR_OPTIONS = tuple((c, c.title()) for c in
                          ["BLK", "BLU", "BRO", "GRY", "GRN", "HAZ", "MAR", "PNK", "DIC", "UNK"])

HAIR_COLOR_OPTIONS = tuple((c, c.title()) for c in
                           ["BAL", "BLK", "BLN", "BRO", "GRY", "RED", "SDY", "WHI", "UNK"])

YES_NO = (("yes", "Yes"), ("no", "No"))

# Core fields common to every state.  State profiles may extend the list.
CORE_FIELDS = (
    FieldDef("state", "", "State", required=True, kind="select",
             description="Jurisdiction selector — drives subfile order, geometry and defaults."),
    FieldDef("customer_id", "DAQ", "License Number", required=True, example="WDL123456789",
             description="Unique driver license number"),
    FieldDef("first_name", "DAC", "First Name", required=True, example="JOHN"),
    FieldDef("last_name", "DCS", "Last Name", required=True, example="SMITH"),
    FieldDef("middle_name", "DAD", "Middle Name", example="ROBERT"),
    FieldDef("suffix", "DCU", "Name Suffix", max_length=5),
    FieldDef("birth_date", "DBB", "Birth Date", required=True, kind="date",
             example="1985-03-15"),
    FieldDef("sex", "DBC", "Sex", required=True, kind="select", options=SEX_OPTIONS),
    FieldDef("eye_color", "DAY", "Eye Color", required=True, kind="select",
             options=EYE_COLOR_OPTIONS),
    FieldDef("hair_color", "DAZ", "Hair Color", kind="select", options=HAIR_COLOR_OPTIONS),
    FieldDef("height", "DAU", "Height", required=True, example="5-10 or 70"),
    FieldDef("weight", "DAW", "Weight (lbs)", example="180", uppercase=False),
    FieldDef("address_street", "DAG", "Street Address", required=True, example="123 MAIN ST"),
    FieldDef("address_city", "DAI", "City", required=True, example="SEATTLE"),
    FieldDef("address_state", "DAJ", "State", required=True, example="WA",
             description="Auto-synced from the jurisdiction selector."),
    FieldDef("address_zip", "DAK", "ZIP Code", required=True, example="98101", uppercase=False),
    FieldDef("class", "DCA", "License Class", example="C", auto_default="NONE", max_length=3),
    FieldDef("restrictions", "DCB", "Restrictions", example="B or NONE", auto_default="NONE"),
    FieldDef("endorsements", "DCC", "Endorsements", example="NONE", auto_default="NONE"),
    FieldDef("issue_date", "DBD", "Issue Date", required=True, kind="date", example="2024-03-15"),
    FieldDef("expiration_date", "DBA", "Expiration Date", required=True, kind="date",
             example="2028-03-15"),
    FieldDef("document_discriminator", "DCF", "Document Discriminator", required=True,
             example="12345678901234567890"),
    # REAL ID COMPLIANT dropdown: UI sends yes/no; backend maps yes -> 'R'.
    FieldDef("compliance_type", "DDA", "REAL ID COMPLIANT", kind="select",
             options=(("no", "No — standard state license"),
                      ("yes", "Yes — REAL ID compliant")),
             auto_default="N", uppercase=False,
             description="Selecting Yes emits DDA=R (REAL ID); No emits DDA=N."),
    FieldDef("organ_donor", "DDK", "Organ Donor", kind="select", options=YES_NO,
             uppercase=False),
    FieldDef("veteran", "DDL", "Veteran", kind="select", options=YES_NO, uppercase=False),
)


def fields_as_dicts():
    """Serialize the shared schema for /api/fields."""
    return [
        {
            "key": f.key,
            "element_id": f.element_id,
            "label": f.label,
            "required": f.required,
            "example": f.example,
            "description": f.description,
            "kind": f.kind,
            "options": [{"value": v, "label": l} for v, l in f.options],
            "max_length": f.max_length,
            "auto_default": f.auto_default,
        }
        for f in CORE_FIELDS
    ]
