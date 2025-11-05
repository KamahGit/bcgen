"""
AAMVA PDF417 Barcode Generator
Compliant with AAMVA DL/ID Card Design Standard
Specifically configured for Washington State Driver's Licenses
"""

from datetime import datetime
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
    Specifically configured for Washington State.
    """
    
    def __init__(self):
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
        barcode_data = "@" + LF
        barcode_data += "\x1e\r"
        barcode_data += "ANSI "
        jurisdiction_code = license_data.get('jurisdiction_code', self.formatter.WA_JURISDICTION_CODE)
        barcode_data += jurisdiction_code
        barcode_data += self.formatter.AAMVA_VERSION
        jurisdiction_version = license_data.get('jurisdiction_version', '00')
        barcode_data += jurisdiction_version.zfill(2)
        barcode_data += f"{1:02d}"
        barcode_data += "DL"
        offset = len(barcode_data) + 8
        barcode_data += f"{offset:04d}"
        length = len(subfile_data)
        barcode_data += f"{length:04d}"
        barcode_data += subfile_data
        # End with carriage return (no trailing LF)
        barcode_data = barcode_data.rstrip("\n") + "\r"
        return barcode_data
    
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

        def clean(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            return str(value).strip().upper()

        def add_line(element_id: str, value: Optional[str], prefix: str = "") -> None:
            if value is None or value == "":
                return
            element = self._build_data_element(element_id, value)
            if prefix:
                element = prefix + element
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
        if last_name and len(last_name) > 35:
            add_line('DCL', self.formatter.truncate_name(last_name))
        if first_name and len(first_name) > 35:
            add_line('DCM', self.formatter.truncate_name(first_name))
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
        add_line('DAK', self.formatter.format_zip(license_data['address_zip']))

        # Customer ID - DAQ
        add_line('DAQ', clean(license_data.get('customer_id')))

        # Document Discriminator - DCF
        document_discriminator = clean(license_data.get('document_discriminator'))
        add_line('DCF', document_discriminator)

        # Country Identification - DCG
        country = clean(license_data.get('country_id')) or 'USA'
        add_line('DCG', country)

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
        card_revision_raw = license_data.get('card_revision_date', '2019-11-12')
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

        # Assemble without leading separator so subfile data begins immediately after header
        return LF.join(lines) + LF
    
    def _build_data_element(self, element_id: str, value: str) -> str:
        """Build a data element in AAMVA format."""
        return f"{element_id}{value}"
    
    def validate_data(self, license_data: Dict) -> tuple[bool, list]:
        """
        Validate that all required fields are present.
        
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
        for field in required_fields:
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


def create_wa_license_barcode(license_data: Dict) -> str:
    """
    Convenience function to create a Washington state license barcode.
    
    Args:
        license_data: Dictionary with license information
        
    Returns:
        Barcode data string ready for PDF417 encoding
    """
    generator = AAMVAPDF417Generator()
    
    # Validate data
    is_valid, errors = generator.validate_data(license_data)
    if not is_valid:
        raise ValueError(f"Invalid license data: {', '.join(errors)}")
    
    return generator.generate_barcode_data(license_data)


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
