"""
AAMVA PDF417 Barcode Generator
Compliant with AAMVA DL/ID Card Design Standard
Includes Washington and sample-based Texas driver-license profiles
"""

from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional
import re


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
    def format_zip(
        zip_code: str,
        padding_length: Optional[int] = 11,
    ) -> str:
        """
        Format a ZIP code as digits, optionally padding it to a fixed width.
        """
        digits = re.sub(r'\D', '', zip_code or '')
        if len(digits) < 5:
            raise ValueError(f"Invalid ZIP code: {zip_code}")

        formatted = digits[:9]
        return formatted.ljust(padding_length) if padding_length is not None else formatted

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


@dataclass(frozen=True)
class AAMVAStateProfile:
    """State-specific settings and supported element order for an AAMVA subfile."""

    name: str
    jurisdiction_code: str
    aamva_version: str
    element_order: tuple[str, ...]
    required_fields: tuple[str, ...]
    subfile_designator: str = 'DL'
    jurisdiction_version: str = '00'
    card_revision_date: Optional[str] = '2019-11-12'
    subfile_terminator: str = '\r'
    zip_padding_length: Optional[int] = 11
    truncated_last_name_element: Optional[str] = 'DCL'
    truncated_first_name_element: Optional[str] = 'DCM'
    additional_element_fields: tuple[tuple[str, str], ...] = ()
    additional_subfiles: tuple['AAMVAAdditionalSubfile', ...] = ()


@dataclass(frozen=True)
class AAMVAAdditionalSubfile:
    """An additional jurisdiction-defined subfile and its static elements."""

    designator: str
    elements: tuple[tuple[str, str], ...]
    terminator: str = '\r'

    def render(self) -> str:
        return self.designator + ''.join(
            element_id + value for element_id, value in self.elements
        ) + self.terminator


WA_PROFILE = AAMVAStateProfile(
    name='WA',
    jurisdiction_code=AAMVADataFormatter.WA_JURISDICTION_CODE,
    aamva_version=AAMVADataFormatter.AAMVA_VERSION,
    element_order=(
        'DCA', 'DCB', 'DCD', 'DBA', 'DCS', 'DAC', 'DAD', 'DCL', 'DCM',
        'DCU', 'DBD', 'DBB', 'DBC', 'DAY', 'DAZ', 'DAU', 'DAG', 'DAI',
        'DAJ', 'DAK', 'DAQ', 'DCF', 'DCG', 'DDE', 'DDF', 'DDG', 'DCJ',
        'DDA', 'DDB', 'DAW', 'DDJ', 'DDK', 'DDL',
    ),
    required_fields=(
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
    ),
)

TX_PROFILE = AAMVAStateProfile(
    name='TX',
    jurisdiction_code='636015',
    aamva_version='09',
    element_order=(
        'DCA', 'DCB', 'DCD', 'DBA', 'DCS', 'DDE', 'DAC', 'DDF', 'DAD',
        'DDG', 'DBD', 'DBB', 'DBC', 'DAY', 'DAU', 'DAG', 'DAI', 'DAJ',
        'DAK', 'DAQ', 'DCF', 'DCG', 'DAZ', 'DCK', 'DCL', 'DDA', 'DDB',
        'DAW',
    ),
    required_fields=WA_PROFILE.required_fields,
    card_revision_date=None,
    subfile_terminator='\n\r',
    zip_padding_length=None,
    truncated_last_name_element=None,
    truncated_first_name_element=None,
    additional_element_fields=(
        ('audit_information', 'DCK'),
        ('race', 'DCL'),
    ),
    additional_subfiles=(
        AAMVAAdditionalSubfile(
            designator='ZT',
            elements=(('ZTA', 'N'),),
        ),
    ),
)


class AAMVAPDF417Generator:
    """
    Generates AAMVA PDF417 barcode data using a jurisdiction-specific profile.
    """
    
    def __init__(self, profile: AAMVAStateProfile = WA_PROFILE):
        self.profile = profile
        self.formatter = AAMVADataFormatter()
    
    def generate_barcode_data(self, license_data: Dict) -> str:
        """
        Generate the complete barcode data string.
        
        Args:
            license_data: Dictionary containing all license information
            
        Returns:
            Formatted string ready for PDF417 encoding
        """
        LF = "\n"
        subfile_data = self._build_subfile_data(license_data, LF)
        primary_data = (
            subfile_data.rstrip(LF) + self.profile.subfile_terminator
        )
        subfiles = [
            (self.profile.subfile_designator, primary_data),
            *(
                (subfile.designator, subfile.render())
                for subfile in self.profile.additional_subfiles
            ),
        ]
        barcode_header = "@" + LF
        barcode_header += "\x1e\r"
        barcode_header += "ANSI "
        jurisdiction_code = license_data.get(
            'jurisdiction_code', self.profile.jurisdiction_code
        )
        barcode_header += jurisdiction_code
        barcode_header += self.profile.aamva_version
        jurisdiction_version = license_data.get(
            'jurisdiction_version', self.profile.jurisdiction_version
        )
        barcode_header += jurisdiction_version.zfill(2)
        barcode_header += f"{len(subfiles):02d}"

        next_offset = len(barcode_header) + 10 * len(subfiles)
        directory = []
        for designator, payload in subfiles:
            directory.append(
                f"{designator}{next_offset:04d}{len(payload):04d}"
            )
            next_offset += len(payload)

        return barcode_header + ''.join(directory) + ''.join(
            payload for _, payload in subfiles
        )
    
    def _build_subfile_data(self, license_data: Dict, LF: str) -> str:
        """
        Build the subfile data section with all data elements.
        
        Args:
            license_data: Dictionary containing all license information
            LF: Line feed character
            
        Returns:
            Formatted subfile data string
        """
        lines = []
        element_ids = []
        element_order = {
            element_id: index
            for index, element_id in enumerate(self.profile.element_order)
        }

        def clean(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            return str(value).strip().upper()

        def add_line(element_id: str, value: Optional[str], prefix: str = "") -> None:
            if value is None or value == "" or element_id not in element_order:
                return
            element = self._build_data_element(element_id, value)
            if prefix:
                element = prefix + element
            element_ids.append(element_id)
            lines.append(element)

        # Jurisdiction-specific class/restrictions/endorsements (with defaults)
        license_class = clean(license_data.get('class')) or 'NONE'
        add_line('DCA', license_class, prefix='DL')

        restrictions = clean(license_data.get('restrictions')) or 'NONE'
        add_line('DCB', restrictions)

        endorsements = clean(license_data.get('endorsements')) or 'NONE'
        add_line('DCD', endorsements)

        # Expiration Date - DBA
        add_line('DBA', self.formatter.format_date(license_data['expiration_date']))

        # Names
        last_name = clean(license_data.get('last_name'))
        first_name = clean(license_data.get('first_name'))
        add_line('DCS', last_name)
        add_line('DAC', first_name)

        if license_data.get('middle_name'):
            middle_name = clean(license_data['middle_name'])
            add_line('DAD', middle_name)
        else:
            middle_name = None

        # Truncated names if needed
        if (
            last_name
            and len(last_name) > 35
            and self.profile.truncated_last_name_element
        ):
            add_line(
                self.profile.truncated_last_name_element,
                self.formatter.truncate_name(last_name),
            )
        if (
            first_name
            and len(first_name) > 35
            and self.profile.truncated_first_name_element
        ):
            add_line(
                self.profile.truncated_first_name_element,
                self.formatter.truncate_name(first_name),
            )
        if license_data.get('suffix'):
            add_line('DCU', clean(license_data['suffix']))

        # Issue Date and Birth Date
        issue_date = license_data.get('issue_date')
        if issue_date:
            add_line('DBD', self.formatter.format_date(issue_date))

        add_line('DBB', self.formatter.format_date(license_data['birth_date']))

        # Sex - DBC
        sex_code = self.formatter.SEX_CODES.get(
            (license_data.get('sex') or 'U').upper(), '9'
        )
        add_line('DBC', sex_code)

        # Eye Color - DAY
        eye_code_input = clean(license_data.get('eye_color')) or 'UNK'
        eye_code = self.formatter.EYE_COLOR_CODES.get(eye_code_input, eye_code_input)
        add_line('DAY', eye_code)

        hair_code_input = clean(license_data.get('hair_color'))
        if hair_code_input:
            hair_code = self.formatter.HAIR_COLOR_CODES.get(hair_code_input, hair_code_input)
            add_line('DAZ', hair_code)

        # Height - DAU
        height = self.formatter.format_height(license_data['height'])
        add_line('DAU', height)

        # Address details
        add_line('DAG', clean(license_data.get('address_street')))
        add_line('DAI', clean(license_data.get('address_city')))
        add_line('DAJ', clean(license_data.get('address_state')))
        add_line(
            'DAK',
            self.formatter.format_zip(
                license_data['address_zip'],
                self.profile.zip_padding_length,
            ),
        )

        # Customer ID - DAQ
        add_line('DAQ', clean(license_data.get('customer_id')))

        # Document Discriminator - DCF
        document_discriminator = clean(license_data.get('document_discriminator'))
        add_line('DCF', document_discriminator)

        # Country Identification - DCG
        country = clean(license_data.get('country_id')) or 'USA'
        add_line('DCG', country)

        for field_name, element_id in self.profile.additional_element_fields:
            add_line(element_id, clean(license_data.get(field_name)))

        # Jurisdiction-specific compliance flags (defaults to 'N')
        dde = clean(license_data.get('jurisdiction_endorsement_expiration')) or 'N'
        ddf = clean(license_data.get('jurisdiction_endorsement_code')) or 'N'
        ddg = clean(license_data.get('jurisdiction_restriction_code')) or 'N'
        add_line('DDE', dde)
        add_line('DDF', ddf)
        add_line('DDG', ddg)

        # Jurisdiction-specific identifier (DCJ)
        dcj_value = clean(license_data.get('inventory_control'))
        if not dcj_value and document_discriminator:
            # Split document_discriminator at license number, use the part after as DCJ
            # Assume format: <license_number><audit_code>
            license_number = clean(license_data.get('customer_id'))
            if license_number and document_discriminator.startswith(license_number):
                dcj_value = document_discriminator[len(license_number):]
            else:
                dcj_value = document_discriminator
        add_line('DCJ', dcj_value)

        # Compliance type - DDA (default 'N')
        compliance_type = clean(license_data.get('compliance_type')) or 'N'
        add_line('DDA', compliance_type)

        # Card revision date - DDB (default WA baseline 2019-11-12)
        card_revision_raw = license_data.get(
            'card_revision_date', self.profile.card_revision_date
        )
        if card_revision_raw is not None:
            add_line('DDB', self.formatter.format_date(card_revision_raw))

        # Weight (pounds) - DAW
        weight_value = self.formatter.format_weight(
            license_data.get('weight_pounds') or license_data.get('weight')
        )
        if weight_value:
            add_line('DAW', weight_value)

        if license_data.get('under_21_until'):
            add_line('DDJ', self.formatter.format_date(license_data['under_21_until']))

        if 'organ_donor' in license_data:
            donor_code = '1' if license_data.get('organ_donor') else '0'
            add_line('DDK', donor_code)

        if 'veteran' in license_data:
            veteran_code = '1' if license_data['veteran'] else '0'
            add_line('DDL', veteran_code)

        ordered_lines = [
            line
            for _, line in sorted(
                zip(element_ids, lines),
                key=lambda item: element_order[item[0]],
            )
        ]

        # Assemble without leading separator so subfile data begins immediately after header
        return LF.join(ordered_lines) + LF
    
    def _build_data_element(self, element_id: str, value: str) -> str:
        """Build a data element in AAMVA format."""
        return f"{element_id}{value}"
    
    def validate_data(self, license_data: Dict) -> tuple[bool, list]:
        """
        Validate that all required fields are present.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        for field in self.profile.required_fields:
            if field not in license_data or not license_data[field]:
                errors.append(f"Missing required field: {field}")
        
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


def create_license_barcode(
    license_data: Dict,
    profile: AAMVAStateProfile = WA_PROFILE,
) -> str:
    """Validate license data and create a barcode with the selected profile."""
    generator = AAMVAPDF417Generator(profile)
    is_valid, errors = generator.validate_data(license_data)
    if not is_valid:
        raise ValueError(f"Invalid license data: {', '.join(errors)}")
    return generator.generate_barcode_data(license_data)


def create_wa_license_barcode(license_data: Dict) -> str:
    """
    Convenience function to create a Washington state license barcode.
    
    Args:
        license_data: Dictionary with license information
        
    Returns:
        Barcode data string ready for PDF417 encoding
    """
    return create_license_barcode(license_data, WA_PROFILE)


def create_tx_license_barcode(license_data: Dict) -> str:
    """Convenience function to create a Texas license barcode."""
    return create_license_barcode(license_data, TX_PROFILE)


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
        barcode_data = create_wa_license_barcode(sample_license)
        print("Barcode data generated successfully!")
        print("\n" + "="*50)
        print("BARCODE DATA:")
        print("="*50)
        print(barcode_data)
        print("="*50)
        print(f"\nTotal length: {len(barcode_data)} characters")
    except ValueError as e:
        print(f"Error: {e}")
