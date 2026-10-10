"""All 50 states + DC.

Draft status (v2.0.0-alpha.1):
  * WA and MI carry researched DL orderings / geometry / subfile structure.
  * Every other state uses the generic AAMVA DL ordering, default geometry
    (13 columns, auto rows) and no horizontal flip.  These entries are
    placeholders to be refined in later research stages — updating one state
    only means editing its entry here (or creating a dedicated module like
    wa.py / mi.py and registering it).
IINs follow the AAMVA issuer identification number list.
"""

from .base import BarcodeConfig, JurisdictionProfile, SubFileSpec, build_default_profile

# (state, name, iin) — verified AAMVA IINs
_IIN_TABLE = [
    ("AL", "Alabama", "635014"),
    ("AK", "Alaska", "635009"),
    ("AZ", "Arizona", "635011"),
    ("AR", "Arkansas", "635003"),
    ("CA", "California", "635020"),
    ("CO", "Colorado", "635022"),
    ("CT", "Connecticut", "635002"),
    ("DE", "Delaware", "635005"),
    ("DC", "District of Columbia", "635090"),
    ("FL", "Florida", "635038"),
    ("GA", "Georgia", "635039"),
    ("HI", "Hawaii", "635007"),
    ("ID", "Idaho", "635012"),
    ("IL", "Illinois", "635043"),
    ("IN", "Indiana", "635023"),
    ("IA", "Iowa", "635024"),
    ("KS", "Kansas", "635025"),
    ("KY", "Kentucky", "635026"),
    ("LA", "Louisiana", "635027"),
    ("ME", "Maine", "635004"),
    ("MD", "Maryland", "635030"),
    ("MA", "Massachusetts", "635029"),
    ("MI", "Michigan", "636032"),   # overridden by mi.py
    ("MN", "Minnesota", "635031"),
    ("MS", "Mississippi", "635033"),
    ("MO", "Missouri", "635034"),
    ("MT", "Montana", "635035"),
    ("NE", "Nebraska", "635037"),
    ("NV", "Nevada", "635040"),
    ("NH", "New Hampshire", "635013"),
    ("NJ", "New Jersey", "635036"),
    ("NM", "New Mexico", "635041"),
    ("NY", "New York", "635046"),
    ("NC", "North Carolina", "635050"),
    ("ND", "North Dakota", "635049"),
    ("OH", "Ohio", "635051"),
    ("OK", "Oklahoma", "635052"),
    ("OR", "Oregon", "635053"),
    ("PA", "Pennsylvania", "635054"),
    ("RI", "Rhode Island", "635055"),
    ("SC", "South Carolina", "635056"),
    ("SD", "South Dakota", "635057"),
    ("TN", "Tennessee", "635059"),
    ("TX", "Texas", "635060"),
    ("UT", "Utah", "635061"),
    ("VT", "Vermont", "635062"),
    ("VA", "Virginia", "635063"),
    ("WA", "Washington", "636045"),  # overridden by wa.py
    ("WV", "West Virginia", "635065"),
    ("WI", "Wisconsin", "635066"),
    ("WY", "Wyoming", "635067"),
]


def _draft_profiles():
    profiles = {}
    for state, name, iin in _IIN_TABLE:
        if state in ("WA", "MI"):
            continue  # researched modules override these
        p = build_default_profile(state, name, iin)
        p.notes = ("Draft profile (alpha.1): generic DL order and default "
                   "geometry; pending state-specific research.")
        profiles[state] = p
    return profiles


DRAFT_PROFILES = _draft_profiles()
