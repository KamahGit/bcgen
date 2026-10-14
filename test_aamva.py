"""
Unit tests for AAMVA PDF417 barcode generator
"""

import unittest
from datetime import datetime
from dataclasses import replace
from aamva_pdf417 import (
    AAMVAPDF417Generator,
    AAMVADataFormatter,
    WA_PROFILE,
    create_wa_license_barcode,
    create_tx_license_barcode,
)


class TestAAMVADataFormatter(unittest.TestCase):
    """Test the AAMVA data formatter utilities."""
    
    def setUp(self):
        self.formatter = AAMVADataFormatter()
    
    def test_format_date_iso(self):
        """Test ISO date format (YYYY-MM-DD)."""
        result = self.formatter.format_date('1985-03-15')
        self.assertEqual(result, '03151985')
    
    def test_format_date_slash(self):
        """Test slash date format (MM/DD/YYYY)."""
        result = self.formatter.format_date('03/15/1985')
        self.assertEqual(result, '03151985')
    
    def test_format_date_already_formatted(self):
        """Test already formatted date (MMDDYYYY)."""
        result = self.formatter.format_date('03151985')
        self.assertEqual(result, '03151985')
    
    def test_format_date_invalid(self):
        """Test invalid date format."""
        with self.assertRaises(ValueError):
            self.formatter.format_date('invalid-date')
    
    def test_format_height_feet_inches(self):
        """Test height format with feet-inches."""
        result = self.formatter.format_height('5-10')
        self.assertEqual(result, '070 in')
    
    def test_format_height_inches_only(self):
        """Test height format with inches only."""
        result = self.formatter.format_height('72')
        self.assertEqual(result, '072 in')
    
    def test_truncate_name_short(self):
        """Test name truncation with short name."""
        result = self.formatter.truncate_name('SMITH')
        self.assertEqual(result, 'SMITH')
    
    def test_truncate_name_long(self):
        """Test name truncation with long name."""
        long_name = 'A' * 50
        result = self.formatter.truncate_name(long_name, 35)
        self.assertEqual(len(result), 35)
        self.assertEqual(result, 'A' * 35)


class TestAAMVAPDF417Generator(unittest.TestCase):
    """Test the main PDF417 generator."""
    
    def setUp(self):
        self.generator = AAMVAPDF417Generator()
        self.valid_license_data = {
            'customer_id': 'WDL123456789',
            'last_name': 'SMITH',
            'first_name': 'JOHN',
            'middle_name': 'R',
            'birth_date': '1985-03-15',
            'expiration_date': '2028-03-15',
            'issue_date': '2024-03-15',
            'sex': 'M',
            'eye_color': 'BRO',
            'height': '5-10',
            'address_street': '123 MAIN ST',
            'address_city': 'SEATTLE',
            'address_state': 'WA',
            'address_zip': '98101',
            'document_discriminator': '12345678901234567890',
        }
    
    def test_validate_data_valid(self):
        """Test validation with valid data."""
        is_valid, errors = self.generator.validate_data(self.valid_license_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_data_missing_required(self):
        """Test validation with missing required fields."""
        incomplete_data = {
            'customer_id': 'WDL123',
            'last_name': 'SMITH',
            # Missing many required fields
        }
        is_valid, errors = self.generator.validate_data(incomplete_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_data_invalid_date(self):
        """Test validation with invalid date."""
        invalid_data = self.valid_license_data.copy()
        invalid_data['birth_date'] = 'not-a-date'
        is_valid, errors = self.generator.validate_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertTrue(any('birth_date' in e for e in errors))
    
    def test_generate_barcode_data_structure(self):
        """Test that generated barcode has correct structure."""
        barcode_data = self.generator.generate_barcode_data(self.valid_license_data)
        
        # Check compliance indicator
        self.assertTrue(barcode_data.startswith('@'))
        
        # Check ANSI header
        self.assertIn('ANSI', barcode_data)
        
        # Check jurisdiction code (WA = 636045)
        self.assertIn('636045', barcode_data)
        
        # Check version (09)
        self.assertIn('09', barcode_data)
        
        # Check subfile designator
        self.assertIn('DL', barcode_data)
        
        # Check required elements are present
        self.assertIn('DAQ', barcode_data)  # Customer ID
        self.assertIn('DCS', barcode_data)  # Last name
        self.assertIn('DAC', barcode_data)  # First name
        self.assertIn('DBB', barcode_data)  # Birth date
        self.assertIn('DBA', barcode_data)  # Expiration date

    def test_wa_header_and_subfile_order(self):
        """Pin the current WA header and element order before profile refactoring."""
        data = self.valid_license_data.copy()
        data.update({
            'hair_color': 'BRO',
            'weight_pounds': '175',
            'organ_donor': True,
            'veteran': False,
            'class': 'C',
            'restrictions': 'B',
            'endorsements': 'NONE',
        })

        barcode_data = self.generator.generate_barcode_data(data)
        header_start = barcode_data.index('ANSI ') + len('ANSI ')
        header = barcode_data[header_start:header_start + 22]
        self.assertEqual(header, '636045090001DL00310274')

        subfile_data = self.generator._build_subfile_data(data, '\n')
        element_ids = [
            line[2:5] if line.startswith('DL') else line[:3]
            for line in subfile_data.splitlines()
        ]
        self.assertEqual(element_ids, [
            'DCA', 'DCB', 'DCD', 'DBA', 'DCS', 'DAC', 'DAD', 'DBD',
            'DBB', 'DBC', 'DAY', 'DAZ', 'DAU', 'DAG', 'DAI', 'DAJ',
            'DAK', 'DAQ', 'DCF', 'DCG', 'DDE', 'DDF', 'DDG', 'DCJ',
            'DDA', 'DDB', 'DAW', 'DDK', 'DDL',
        ])

    def test_profile_configures_header_and_element_order(self):
        profile = replace(
            WA_PROFILE,
            name='TEST',
            jurisdiction_code='123456',
            element_order=('DAQ', 'DCS', 'DAC'),
            required_fields=('customer_id', 'last_name', 'first_name'),
        )
        generator = AAMVAPDF417Generator(profile)
        data = self.valid_license_data.copy()
        data['hair_color'] = 'BRO'
        barcode_data = generator.generate_barcode_data(data)
        self.assertEqual(
            generator.validate_data({
                'customer_id': 'TEST123',
                'last_name': 'SMITH',
                'first_name': 'JANE',
            }),
            (True, []),
        )

        header_start = barcode_data.index('ANSI ') + len('ANSI ')
        header = barcode_data[header_start:header_start + 22]
        self.assertEqual(header[:14], '123456090001DL')

        subfile_data = generator._build_subfile_data(data, '\n')
        element_ids = [
            line[2:5] if line.startswith('DL') else line[:3]
            for line in subfile_data.splitlines()
        ]
        self.assertEqual(element_ids, ['DAQ', 'DCS', 'DAC'])
        self.assertNotIn('DAZ', element_ids)
        self.assertEqual(
            int(header[14:18]),
            len(barcode_data) - len(subfile_data),
        )
        self.assertEqual(int(header[18:22]), len(subfile_data))

    def test_texas_profile_matches_sample_header_order_and_subfiles(self):
        data = {
            'customer_id': '47136971',
            'last_name': 'DUCK',
            'first_name': 'DONALD',
            'middle_name': 'MICHAEL',
            'birth_date': '1996-07-13',
            'expiration_date': '2029-07-13',
            'issue_date': '2021-10-07',
            'sex': 'M',
            'eye_color': 'BRO',
            'hair_color': 'BLK',
            'height': '81',
            'address_street': '1235 HARTSDALE DR APT 205',
            'address_city': 'DALLAS',
            'address_state': 'TX',
            'address_zip': '75211-0000',
            'document_discriminator': '42629181100007475796',
            'audit_information': '10009788126',
            'race': 'BKO',
            'compliance_type': 'F',
            'card_revision_date': '2020-02-23',
            'weight_pounds': '270',
            'class': 'C',
        }
        barcode_data = create_tx_license_barcode(data)

        expected_dl_lines = [
            'DLDCAC', 'DCBNONE', 'DCDNONE', 'DBA07132029', 'DCSDUCK',
            'DDEN', 'DACDONALD', 'DDFN', 'DADMICHAEL', 'DDGN',
            'DBD10072021', 'DBB07131996', 'DBC1', 'DAYBRO', 'DAU081 in',
            'DAG1235 HARTSDALE DR APT 205', 'DAIDALLAS', 'DAJTX',
            'DAK752110000', 'DAQ47136971', 'DCF42629181100007475796',
            'DCGUSA', 'DAZBLK', 'DCK10009788126', 'DCLBKO', 'DDAF',
            'DDB02232020', 'DAW270',
        ]
        expected = (
            '@\n\x1e\rANSI 636015090002DL00410280ZT03210007'
            + '\n'.join(expected_dl_lines)
            + '\n\rZTZTAN\r'
        )
        self.assertEqual(barcode_data, expected)
    
    def test_generate_barcode_data_values(self):
        """Test that values are correctly included in barcode."""
        barcode_data = self.generator.generate_barcode_data(self.valid_license_data)
        
        # Check actual values are present
        self.assertIn('WDL123456789', barcode_data)
        self.assertIn('SMITH', barcode_data)
        self.assertIn('JOHN', barcode_data)
        self.assertIn('SEATTLE', barcode_data)
        self.assertIn('98101', barcode_data)
    
    def test_generate_barcode_with_optional_fields(self):
        """Test generation with optional fields."""
        data_with_optional = self.valid_license_data.copy()
        data_with_optional.update({
            'hair_color': 'BRO',
            'weight_pounds': '175',
            'organ_donor': True,
            'veteran': False,
            'class': 'C',
            'restrictions': 'B',
            'endorsements': 'NONE',
        })
        
        barcode_data = self.generator.generate_barcode_data(data_with_optional)
        
        # Check optional elements
        self.assertIn('DAZ', barcode_data)  # Hair color
        self.assertIn('DAW', barcode_data)  # Weight
        self.assertIn('DDK', barcode_data)  # Organ donor
        self.assertIn('DDL', barcode_data)  # Veteran
        self.assertIn('DCA', barcode_data)  # Class
    
    def test_sex_code_conversion(self):
        """Test sex code conversion."""
        test_cases = {
            'M': '1',
            'F': '2',
            'X': '9',
            'U': '9',
        }
        
        for sex, expected_code in test_cases.items():
            data = self.valid_license_data.copy()
            data['sex'] = sex
            barcode_data = self.generator.generate_barcode_data(data)
            self.assertIn(f'DBC{expected_code}', barcode_data)
    
    def test_build_data_element(self):
        """Test data element building."""
        result = self.generator._build_data_element('DAQ', 'WDL123')
        self.assertEqual(result, 'DAQWDL123')


class TestConvenienceFunction(unittest.TestCase):
    """Test the convenience function."""
    
    def test_create_wa_license_barcode_valid(self):
        """Test creating barcode with valid data."""
        valid_data = {
            'customer_id': 'WDL999888777',
            'last_name': 'DOE',
            'first_name': 'JANE',
            'birth_date': '1990-06-20',
            'expiration_date': '2029-06-20',
            'sex': 'F',
            'eye_color': 'BLU',
            'height': '5-6',
            'address_street': '456 ELM ST',
            'address_city': 'TACOMA',
            'address_state': 'WA',
            'address_zip': '98402',
            'document_discriminator': '99988877766655544433',
        }
        
        barcode_data = create_wa_license_barcode(valid_data)
        self.assertIsInstance(barcode_data, str)
        self.assertGreater(len(barcode_data), 0)
    
    def test_create_wa_license_barcode_invalid(self):
        """Test creating barcode with invalid data."""
        invalid_data = {'customer_id': 'TEST'}  # Missing required fields
        
        with self.assertRaises(ValueError):
            create_wa_license_barcode(invalid_data)

    def test_create_tx_license_barcode_invalid(self):
        with self.assertRaises(ValueError):
            create_tx_license_barcode({'customer_id': 'TEST'})


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def test_empty_middle_name(self):
        """Test with empty middle name."""
        generator = AAMVAPDF417Generator()
        data = {
            'customer_id': 'WDL123456789',
            'last_name': 'SMITH',
            'first_name': 'JOHN',
            'middle_name': '',
            'birth_date': '1985-03-15',
            'expiration_date': '2028-03-15',
            'sex': 'M',
            'eye_color': 'BRO',
            'height': '70',
            'address_street': '123 MAIN ST',
            'address_city': 'SEATTLE',
            'address_state': 'WA',
            'address_zip': '98101',
            'document_discriminator': '12345678901234567890',
        }
        
        barcode_data = generator.generate_barcode_data(data)
        self.assertIsInstance(barcode_data, str)
    
    def test_long_name_truncation(self):
        """Test name truncation in barcode generation."""
        generator = AAMVAPDF417Generator()
        data = {
            'customer_id': 'WDL123456789',
            'last_name': 'A' * 50,  # Very long name
            'first_name': 'B' * 50,
            'birth_date': '1985-03-15',
            'expiration_date': '2028-03-15',
            'sex': 'M',
            'eye_color': 'BRO',
            'height': '70',
            'address_street': '123 MAIN ST',
            'address_city': 'SEATTLE',
            'address_state': 'WA',
            'address_zip': '98101',
            'document_discriminator': '12345678901234567890',
        }
        
        # Should not raise an error
        barcode_data = generator.generate_barcode_data(data)
        self.assertIsInstance(barcode_data, str)


if __name__ == '__main__':
    unittest.main()
