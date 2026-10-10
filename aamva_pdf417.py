"""
AAMVA PDF417 Barcode Generator
Compliant with AAMVA DL/ID Card Design Standard
Multi-jurisdiction (all 50 US states + DC) — v2.0.0-alpha.1

State-specific behavior (DL element order, jurisdiction subfiles like ZM/ZW,
PDF417 rows/columns, WA-only horizontal flip) is driven by JurisdictionProfile
objects in the `states` package.  The generator itself is state-agnostic.
"""

from datetime import datetime
from typing import Dict, List, Optional
import re

from states import (
    ELEMENT_DELIMITER,
    SUBFILE_DELIMITER,
    JurisdictionProfile,
    SubFileSpec,
    get_profile,
)

VERSION = "2.0.0-alpha.1"


class AAMVADataFormatter:
    """
    Formats driver's license data according to AAMVA standards.
    """
    
    # AAMVA Data Element IDs
    ELEMENT_IDS = {
        # Mandatory elements
        'jurisdiction_code': 'DCJ',
        'customer_id': 'DAQ',
        'last_name': 'DCS',
        'first_name': 'DAC',
        'expiration_date': 'DBA',
        'birth_date': 'DBB',
        'sex': 'DBC',
        'eye_color': 'DAY',
        'height': 'DAU',
        'address_street': 'DAG',
        'address_city': 'DAI',
        'address_state': 'DAJ',
        'address_zip': 'DAK',
        'document_discriminator': 'DCF',
        'country_id': 'DCG',
        'family_name': 'DCL',  # Truncated last name
        'given_name': 'DCM',    # Truncated first name
        'suffix': 'DCU',
        
        # Optional elements
        'weight_range': 'DCE',
        'middle_name': 'DAD',
        'hair_color': 'DAZ',
        'place_of_birth': 'DCI',
        'audit_information': 'DCK',
        'inventory_control': 'DCJ',
        'alias': 'DBN',
        'name_suffix': 'DCU',
        'name_prefix': 'DCO',
        'issue_date': 'DBD',
        'revision_date': 'DCD',
        'race': 'DCL',
        'compliance_type': 'DDA',
        'card_revision_date': 'DDB',
        'hazmat_endorsement_expiry': 'DDC',
        'limited_duration': 'DDD',
        'weight_pounds': 'DAW',
        'weight_kilograms': 'DAX',
        'under_18_until': 'DDH',
        'under_19_until': 'DDI',
        'under_21_until': 'DDJ',
        'organ_donor': 'DDK',
        'veteran': 'DDL',
    }
    
    # Washington State specific
    WA_JURISDICTION_CODE = '636045'
    AAMVA_VERSION = '09'  # Version 9 (2016 standard)
    
    # Sex codes
    SEX_CODES = {'M': '1', 'F': '2', 'X': '9', 'U': '9'}
    
    # Eye color codes
    EYE_COLOR_CODES = {
        'BLK': 'BLK',  # Black
        'BLU': 'BLU',  # Blue
        'BRO': 'BRO',  # Brown
        'GRY': 'GRY',  # Gray
        'GRN': 'GRN',  # Green
        'HAZ': 'HAZ',  # Hazel
        'MAR': 'MAR',  # Maroon
        'PNK': 'PNK',  # Pink
        'DIC': 'DIC',  # Dichromatic
        'UNK': 'UNK',  # Unknown
    }
    
    # Hair color codes
    HAIR_COLOR_CODES = {
        'BAL': 'BAL',  # Bald
        'BLK': 'BLK',  # Black
        'BLN': 'BLN',  # Blond
        'BRO': 'BRO',  # Brown
        'GRY': 'GRY',  # Grey
        'RED': 'RED',  # Red/Auburn
        'SDY': 'SDY',  # Sandy
        'WHI': 'WHI',  # White
        'UNK': 'UNK',  # Unknown
    }
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """
        Format date to MMDDCCYY format required by AAMVA.
        Input can be YYYY-MM-DD, MM/DD/YYYY, or already formatted.
        """
        # Try to parse various date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m%d%Y']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%m%d%Y')
            except ValueError:
                continue
        
        # If already in correct format, return as is
        if re.match(r'^\d{8}$', date_str):
            return date_str
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    @staticmethod
    def format_height(height_str: str) -> str:
        """
        Format height to AAMVA standard.
        Input: feet-inches (e.g., "5-10") or inches (e.g., "70")
        Output: total inches with leading zero if needed (e.g., "070 in")
        """
        if '-' in height_str:
            feet, inches = height_str.split('-')
            total_inches = int(feet) * 12 + int(inches)
        else:
            total_inches = int(height_str)
        
        return f"{total_inches:03d} in"
    
    @staticmethod
    def truncate_name(name: str, max_length: int = 35) -> str:
        """Truncate name if exceeds maximum length."""
        return name[:max_length] if len(name) > max_length else name

    @staticmethod
    def format_zip(zip_code: str) -> str:
        """
        Format ZIP code to AAMVA standard (11 characters, digits plus padding).
        Accepts 5 or 9 digit ZIP (with or without separators).
        """
        digits = re.sub(r'\D', '', zip_code or '')
        if len(digits) < 5:
            raise ValueError(f"Invalid ZIP code: {zip_code}")

        base = digits[:5]
        extension = digits[5:9]
        formatted = base + extension
        return formatted.ljust(11)

    @staticmethod
    def format_weight(weight_value: Optional[str]) -> Optional[str]:
        """Format weight in pounds as a three-digit numeric string without units."""
        if not weight_value:
            return None

        try:
            digits = re.sub(r'[^0-9]', '', str(weight_value))
            if not digits:
                return None
            return str(int(digits))
        except ValueError as exc:
            raise ValueError(f"Invalid weight: {weight_value}") from exc


class AAMVAPDF417Generator:
    """
    Generates AAMVA-compliant PDF417 barcode data for driver's licenses.
    State-agnostic: every jurisdiction-specific decision is taken from the
    profile passed in (or resolved from license_data['state']).
    """

    def __init__(self, profile: Optional[JurisdictionProfile] = None):
        self.formatter = AAMVADataFormatter()
        self.profile = profile

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate_barcode_data(self, license_data: Dict) -> str:
        """
        Generate the complete barcode data string for the license's state.

        Layout produced (matches real-world dumps, e.g. Michigan):
          @<LF>\x1eCR ANSI <iin><ver><jver><nc>#<typeID><offset><len>... \
          <subfile1 data><CR><subfile2 data>...<CR>
        Offsets/lengths for every subfile are computed AFTER the subfiles are
        built, then the ANSI header is assembled with those values.
        """
        profile = self._resolve_profile(license_data)

        # 1. Build each subfile body ("DL..." prefix + LF-separated elements).
        bodies = [self._build_subfile_body(profile, sf, license_data)
                  for sf in profile.subfiles]
        combined = SUBFILE_DELIMITER.join(bodies) + ELEMENT_DELIMITER

        # 2. Fixed-width header portion: "ANSI " + iin(6)+ver(2)+jver(2)+count(2)
        header_prefix = "ANSI " + profile.iin + profile.aamva_version + \
            license_data.get('jurisdiction_version', profile.jurisdiction_version).zfill(2) + \
            f"{len(profile.subfiles):02d}"

        # 3. Compute offsets/lengths iteratively (each descriptor is exactly
        #    8 chars: 4-digit offset + 4-digit length).  Offsets are measured
        #    from the start of the ANSI line (verified against real MI/WA dumps).
        descriptors = []
        running_offset = len(header_prefix) + 8 * len(profile.subfiles)
        for sf, body in zip(profile.subfiles, bodies):
            descriptors.append((sf.type_id, running_offset, len(body)))
            running_offset += len(body) + 1   # +1 for the CR delimiter

        header = header_prefix
        for type_id, offset, length in descriptors:
            header += f"{type_id}{offset:04d}{length:04d}"

        barcode_data = "@" + ELEMENT_DELIMITER + "\x1e" + header + combined
        # End with carriage return (no trailing LF)
        barcode_data = barcode_data.rstrip(ELEMENT_DELIMITER) + "\r"
        return barcode_data

    def validate_data(self, license_data: Dict) -> tuple:
        """
        Validate that all required fields are present for the license's state.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        required_fields = [
            'customer_id',
            'last_name',
            'first_name',
            'birth_date',
            'expiration_date',
            'sex',
            'eye_color',
            'height',
            'address_street',
            'address_city',
            'address_state',
            'address_zip',
            'document_discriminator',
        ]

        errors = []
        profile = None
        try:
            profile = self._resolve_profile(license_data)
        except ValueError as e:
            errors.append(str(e))

        for field in required_fields:
            if field not in license_data or not license_data[field]:
                errors.append(f"Missing required field: {field}")

        if profile is not None:
            for field in profile.mandatory_fields:
                if not license_data.get(field):
                    errors.append(f"Missing required field for {profile.state}: {field}")

        # Validate date formats
        date_fields = ['birth_date', 'expiration_date']
        if 'issue_date' in license_data:
            date_fields.append('issue_date')

        for field in date_fields:
            if field in license_data:
                try:
                    self.formatter.format_date(license_data[field])
                except ValueError as e:
                    errors.append(f"Invalid {field}: {str(e)}")

        return len(errors) == 0, errors

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _resolve_profile(self, license_data: Dict) -> JurisdictionProfile:
        if self.profile is not None:
            return self.profile
        state = license_data.get('state') or license_data.get('address_state') \
            or license_data.get('jurisdiction_code')
        if not state:
            raise ValueError("No state specified: set 'state' in the license data")
        return get_profile(state)

    def _build_subfile_body(self, profile: JurisdictionProfile,
                            sf: SubFileSpec, license_data: Dict) -> str:
        """Emit one subfile: '<TYPEID>' followed by its ordered elements,
        separated by line feeds.  Ordering comes entirely from the profile."""
        lines = [sf.type_id]
        for element_id in sf.element_order:
            value = self._compute_element(profile, sf, element_id, license_data)
            if value is None or value == "":
                continue
            lines.append(f"{element_id}{value}")
        return ELEMENT_DELIMITER.join(lines)

    def _compute_element(self, profile: JurisdictionProfile, sf: SubFileSpec,
                         element_id: str, license_data: Dict) -> Optional[str]:
        """Resolve the value for one element id in one subfile."""
        # Jurisdiction-specific subfiles (ZW/ZM/...): raw dict of element->text
        extras_key = f"{sf.type_id.lower()}_elements"
        if extras_key in license_data and element_id in license_data[extras_key]:
            return str(license_data[extras_key][element_id])
        if sf.type_id != "DL":
            # Not enough research yet for this element in this subfile.
            return None

        clean = lambda v: None if v is None else str(v).strip().upper()
        fmt = self.formatter

        if element_id == 'DCA':
            return clean(license_data.get('class')) or 'NONE'
        if element_id == 'DCB':
            return clean(license_data.get('restrictions')) or 'NONE'
        if element_id in ('DCC', 'DCD'):
            # Some states put endorsements in DCC, others (WA/MI) in DCD.
            val = clean(license_data.get('endorsements'))
            if val is None:
                return None
            return val or 'NONE'
        if element_id == 'DBA':
            return fmt.format_date(license_data['expiration_date'])
        if element_id == 'DCS':
            return clean(license_data.get('last_name'))
        if element_id == 'DAC':
            return clean(license_data.get('first_name'))
        if element_id == 'DCT':
            return clean(license_data.get('first_name'))
        if element_id == 'DAD':
            return clean(license_data.get('middle_name'))
        if element_id in ('DAE', 'DCU'):
            return clean(license_data.get('suffix'))
        if element_id == 'DBD':
            issue_date = license_data.get('issue_date')
            return fmt.format_date(issue_date) if issue_date else None
        if element_id == 'DBB':
            return fmt.format_date(license_data['birth_date'])
        if element_id == 'DBC':
            return self.formatter.SEX_CODES.get(
                (license_data.get('sex') or 'U').upper(), '9')
        if element_id == 'DAY':
            eye = clean(license_data.get('eye_color')) or 'UNK'
            return fmt.EYE_COLOR_CODES.get(eye, eye)
        if element_id == 'DAZ':
            hair = clean(license_data.get('hair_color'))
            return fmt.HAIR_COLOR_CODES.get(hair, hair) if hair else None
        if element_id == 'DAU':
            return fmt.format_height(license_data['height'])
        if element_id == 'DAW':
            return fmt.format_weight(
                license_data.get('weight_pounds') or license_data.get('weight'))
        if element_id == 'DAG':
            return clean(license_data.get('address_street'))
        if element_id == 'DAI':
            return clean(license_data.get('address_city'))
        if element_id == 'DAJ':
            return clean(license_data.get('address_state'))
        if element_id == 'DAK':
            return fmt.format_zip(license_data['address_zip'])
        if element_id == 'DAH':
            return clean(license_data.get('mail_state'))
        if element_id == 'DCF':
            return clean(license_data.get('document_discriminator'))
        if element_id == 'DCG':
            return clean(license_data.get('country_id')) or 'USA'
        if element_id == 'DCH':
            return clean(license_data.get('jurisdiction_code_text'))
        if element_id in ('DDE',):
            return clean(license_data.get('jurisdiction_endorsement_expiration')) or 'N'
        if element_id == 'DDF':
            return clean(license_data.get('jurisdiction_endorsement_code')) or 'N'
        if element_id == 'DDG':
            return clean(license_data.get('jurisdiction_restriction_code')) or 'N'
        if element_id == 'DCK':
            # Audit information: customer_id + birthdate + expiration (MI style)
            cust = clean(license_data.get('customer_id'))
            if not cust:
                return None
            dob = fmt.format_date(license_data['birth_date'])
            exp = fmt.format_date(license_data['expiration_date'])
            return license_data.get('audit_information') or f"{cust}{dob}{exp}"
        if element_id == 'DCJ':
            dcj = clean(license_data.get('inventory_control'))
            dd = clean(license_data.get('document_discriminator'))
            if not dcj and dd:
                lic = clean(license_data.get('customer_id'))
                if lic and dd.startswith(lic):
                    dcj = dd[len(lic):]
                else:
                    dcj = dd
            return dcj
        if element_id == 'DDA':
            ct = clean(license_data.get('compliance_type')) or 'N'
            # UI sends yes/no for REAL ID COMPLIANT dropdown
            if ct in ('YES', 'TRUE'):
                ct = 'R'
            elif ct in ('NO', 'FALSE'):
                ct = 'N'
            return ct
        if element_id == 'DDB':
            default = profile.card_revision_default or '2019-11-12'
            raw = license_data.get('card_revision_date', default)
            return fmt.format_date(raw)
        if element_id == 'DDJ':
            u21 = license_data.get('under_21_until')
            return fmt.format_date(u21) if u21 else None
        if element_id == 'DDH':
            u18 = license_data.get('under_18_until')
            return fmt.format_date(u18) if u18 else None
        if element_id == 'DDI':
            u19 = license_data.get('under_19_until')
            return fmt.format_date(u19) if u19 else None
        if element_id == 'DDK':
            if 'organ_donor' not in license_data:
                return None
            v = license_data.get('organ_donor')
            b = v not in (False, 0, '0', 'NO', 'FALSE') if isinstance(v, str) else bool(v)
            return '1' if b else '0'
        if element_id == 'DDL':
            if 'veteran' not in license_data:
                return None
            v = license_data.get('veteran')
            b = v not in (False, 0, '0', 'NO', 'FALSE') if isinstance(v, str) else bool(v)
            return '1' if b else '0'
        if element_id in ('DCL',):
            ln = clean(license_data.get('last_name'))
            return fmt.truncate_name(ln) if ln and len(ln) > 35 else None
        if element_id in ('DCM',):
            fn = clean(license_data.get('first_name'))
            return fmt.truncate_name(fn) if fn and len(fn) > 35 else None

        # Unknown element -> allow raw pass-through via data key equal to id.
        return clean(license_data.get(element_id))

    def _build_data_element(self, element_id: str, value: str) -> str:
        """Build a data element in AAMVA format."""
        return f"{element_id}{value}"


def create_license_barcode(license_data: Dict, state: Optional[str] = None) -> str:
    """
    Create a license barcode for any supported US jurisdiction.

    Args:
        license_data: Dictionary with license information
        state: Two-letter state code; overrides license_data['state'] if given

    Returns:
        Barcode data string ready for PDF417 encoding
    """
    if state:
        license_data = {**license_data, 'state': state}
    profile = get_profile(license_data.get('state') or
                          license_data.get('address_state') or '')
    generator = AAMVAPDF417Generator(profile)

    is_valid, errors = generator.validate_data(license_data)
    if not is_valid:
        raise ValueError(f"Invalid license data: {', '.join(errors)}")

    return generator.generate_barcode_data(license_data)


def create_wa_license_barcode(license_data: Dict) -> str:
    """Backwards-compatible wrapper: Washington license barcode."""
    return create_license_barcode({**license_data, 'state': 'WA'})


if __name__ == "__main__":
    # Example usage
    sample_license = {
        'customer_id': 'WDL123456789',
        'last_name': 'SMITH',
        'first_name': 'JOHN',
        'middle_name': 'ROBERT',
        'birth_date': '1985-03-15',
        'expiration_date': '2028-03-15',
        'issue_date': '2024-03-15',
        'sex': 'M',
        'eye_color': 'BRO',
        'hair_color': 'BRO',
        'height': '5-10',
        'weight_pounds': '175',
        'address_street': '123 MAIN ST',
        'address_city': 'SEATTLE',
        'address_state': 'WA',
        'address_zip': '98101',
        'document_discriminator': '12345678901234567890',
        'class': 'C',
        'restrictions': 'NONE',
        'endorsements': 'NONE',
        'compliance_type': 'F',
        'organ_donor': True,
        'veteran': False,
    }
    
    try:
        barcode_data = create_license_barcode(sample_license, state='WA')
        print("WA barcode data generated successfully!")
        print(barcode_data)

        mi_sample = dict(sample_license)
        mi_sample.update({
            'address_state': 'MI', 'address_city': 'ROYAL OAK',
            'address_zip': '48067', 'customer_id': 'P900000331783',
            'zm_elements': {'ZMA': 'Rev 08-16-2021', 'ZMB': '01'},
        })
        mi_data = create_license_barcode(mi_sample, state='MI')
        print("\nMI barcode (DL + ZM subfiles):")
        print(repr(mi_data[:120]))
    except ValueError as e:
        print(f"Error: {e}")
