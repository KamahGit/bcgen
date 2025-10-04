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
        'middle_name': 'DAD',
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
        # Line feed as record separator
        LF = "\n"
        
        # Build subfile data first to calculate length
        subfile_data = self._build_subfile_data(license_data, LF)
        
        # Start with compliance indicator
        barcode_data = "@"
        
        # Add line feed
        barcode_data += LF
        
        # Add ANSI header (note: there's a space after ANSI)
        barcode_data += "ANSI "
        
        # Add jurisdiction code (IIN - Issuer Identification Number)
        jurisdiction_code = license_data.get('jurisdiction_code', 
                                             self.formatter.WA_JURISDICTION_CODE)
        barcode_data += jurisdiction_code
        
        # Add AAMVA version number (2 digits)
        barcode_data += self.formatter.AAMVA_VERSION
        
        # Add number of subfiles (typically 01 for DL/ID)
        barcode_data += "01"
        
        # Subfile designator for DL/ID card (2 chars)
        barcode_data += "DL"
        
        # Calculate offset: from start of file to where subfile data begins
        # Current length + 4 (offset) + 4 (length) = position where data starts
        offset = len(barcode_data) + 8
        barcode_data += f"{offset:04d}"
        
        # Add subfile length (4 decimal digits)
        length = len(subfile_data)
        barcode_data += f"{length:04d}"
        
        # Add the subfile data
        barcode_data += subfile_data
        
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
        # Start subfile data with line feed
        subfile_data = LF
        
        # Add mandatory data elements in recommended order
        # Customer ID Number (license number) - DAQ
        subfile_data += self._build_data_element('DAQ', 
                                                  license_data['customer_id'])
        
        # Family Name (Last Name) - DCS
        subfile_data += LF + self._build_data_element('DCS', 
                                                       license_data['last_name'])
        
        # Given Name (First Name) - DAC
        subfile_data += LF + self._build_data_element('DAC', 
                                                       license_data['first_name'])
        
        # Middle Name (optional) - DAD
        if 'middle_name' in license_data and license_data['middle_name']:
            subfile_data += LF + self._build_data_element('DAD', 
                                                           license_data['middle_name'])
        
        # Date of Birth - DBB
        subfile_data += LF + self._build_data_element('DBB', 
            self.formatter.format_date(license_data['birth_date']))
        
        # Sex - DBC
        sex_code = self.formatter.SEX_CODES.get(
            license_data.get('sex', 'U').upper(), '9')
        subfile_data += LF + self._build_data_element('DBC', sex_code)
        
        # Eye Color - DAY
        eye_color = license_data.get('eye_color', 'UNK').upper()
        subfile_data += LF + self._build_data_element('DAY', eye_color)
        
        # Height - DAU
        height = self.formatter.format_height(license_data['height'])
        subfile_data += LF + self._build_data_element('DAU', height)
        
        # Street Address - DAG
        subfile_data += LF + self._build_data_element('DAG', 
                                                       license_data['address_street'])
        
        # City - DAI
        subfile_data += LF + self._build_data_element('DAI', 
                                                       license_data['address_city'])
        
        # State - DAJ
        subfile_data += LF + self._build_data_element('DAJ', 
                                                       license_data['address_state'])
        
        # Postal Code - DAK
        subfile_data += LF + self._build_data_element('DAK', 
                                                       license_data['address_zip'])
        
        # Country Identification - DCG
        country = license_data.get('country_id', 'USA')
        subfile_data += LF + self._build_data_element('DCG', country)
        
        # Document Discriminator - DCF
        subfile_data += LF + self._build_data_element('DCF', 
                                                       license_data['document_discriminator'])
        
        # Expiration Date - DBA
        subfile_data += LF + self._build_data_element('DBA', 
            self.formatter.format_date(license_data['expiration_date']))
        
        # Issue Date (optional but common) - DBD
        if 'issue_date' in license_data:
            subfile_data += LF + self._build_data_element('DBD', 
                self.formatter.format_date(license_data['issue_date']))
        
        # Jurisdiction-specific vehicle class - DCA
        if 'class' in license_data:
            subfile_data += LF + self._build_data_element('DCA', 
                                                           license_data['class'])
        
        # Jurisdiction-specific restriction codes - DCB
        if 'restrictions' in license_data:
            subfile_data += LF + self._build_data_element('DCB', 
                                                           license_data['restrictions'])
        
        # Jurisdiction-specific endorsement codes - DCD
        if 'endorsements' in license_data:
            subfile_data += LF + self._build_data_element('DCD', 
                                                           license_data['endorsements'])
        
        # Family name truncated - DCL (only if different from DCS)
        family_name = self.formatter.truncate_name(license_data['last_name'])
        if len(license_data['last_name']) > 35:
            subfile_data += LF + self._build_data_element('DCL', family_name)
        
        # Given name truncated - DCM (only if different from DAC)
        given_name = self.formatter.truncate_name(license_data['first_name'])
        if len(license_data['first_name']) > 35:
            subfile_data += LF + self._build_data_element('DCM', given_name)
        
        # Name Suffix - DCU
        if 'suffix' in license_data and license_data['suffix']:
            subfile_data += LF + self._build_data_element('DCU', 
                                                           license_data['suffix'])
        
        # Hair Color - DAZ
        if 'hair_color' in license_data:
            hair_color = license_data['hair_color'].upper()
            subfile_data += LF + self._build_data_element('DAZ', hair_color)
        
        # Weight (pounds) - DAW
        if 'weight_pounds' in license_data:
            weight = f"{int(license_data['weight_pounds']):03d} lb"
            subfile_data += LF + self._build_data_element('DAW', weight)
        
        # Compliance Type - DDA
        if 'compliance_type' in license_data:
            subfile_data += LF + self._build_data_element('DDA', 
                                                           license_data['compliance_type'])
        
        # Card Revision Date - DDB
        if 'card_revision_date' in license_data:
            subfile_data += LF + self._build_data_element('DDB', 
                self.formatter.format_date(license_data['card_revision_date']))
        
        # Under 21 Until - DDJ
        if 'under_21_until' in license_data:
            subfile_data += LF + self._build_data_element('DDJ', 
                self.formatter.format_date(license_data['under_21_until']))
        
        # Organ Donor - DDK
        if 'organ_donor' in license_data:
            donor_code = '1' if license_data['organ_donor'] else '0'
            subfile_data += LF + self._build_data_element('DDK', donor_code)
        
        # Veteran - DDL
        if 'veteran' in license_data:
            veteran_code = '1' if license_data['veteran'] else '0'
            subfile_data += LF + self._build_data_element('DDL', veteran_code)
        
        return subfile_data
    
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
