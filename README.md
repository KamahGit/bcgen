# AAMVA PDF417 Barcode Generator & Decoder

A Python library for generating and decoding AAMVA-compliant PDF417 barcodes for Washington State driver's licenses.

**Verified Configuration:** 15 visible data columns × 17 rows (based on actual WA license)

## Installation

```bash
pip install -r requirements.txt
```

**Required:**
- `pdf417` - PDF417 barcode encoding
- `Pillow` - Image generation and manipulation

**Optional (for decoding):**
- `zxing-cpp` - Barcode decoding
- `numpy` - Image processing

## Quick Start

### Option 1: Web Application (Recommended)

Start the web server:
```bash
./start.sh
# Or manually:
python3 app.py
```

Then open your browser to: **http://localhost:5000**

The web interface provides:
- ✅ Easy form-based data entry
- ✅ Real-time barcode preview
- ✅ Instant download as PNG
- ✅ Field validation
- ✅ Responsive design

### Option 2: Python API

#### Generate a Barcode

```python
from aamva_pdf417 import create_wa_license_barcode
from pdf417_encoder import PDF417Encoder

# License data
license_data = {
    'customer_id': 'WDL123456789',
    'last_name': 'SMITH',
    'first_name': 'JOHN',
    'middle_name': 'ROBERT',
    'birth_date': '1985-03-15',
    'sex': 'M',
    'eye_color': 'BRO',
    'height': '5-10',
    'address_street': '123 MAIN ST',
    'address_city': 'SEATTLE',
    'address_state': 'WA',
    'address_zip': '98101',
    'class': 'C',
    'restrictions': 'B',
    'endorsements': 'NONE',
    'expiration_date': '2028-03-15',
    'issue_date': '2024-03-15',
    'document_discriminator': '12345678901234567890',
}

# Generate and save barcode
barcode_data = create_wa_license_barcode(license_data)
encoder = PDF417Encoder()
encoder.save_barcode(barcode_data, 'license_barcode.png')
```

#### Texas profile (initial sample-based support)

The generator also exposes a Texas profile, based on the supplied synthetic
Texas barcode sample:

```python
from aamva_pdf417 import create_tx_license_barcode

barcode_data = create_tx_license_barcode(license_data)
```

This profile emits the `DL` and `ZT` subfiles and uses Texas-specific ZIP
formatting. It maps `audit_information` to `DCK` and `race` to `DCL`, and emits
the sample's fixed `ZTA=N` value. The web application and CLI still use the
Washington convenience function; state selection there is not yet implemented.

#### Decode a Barcode

```python
from pdf417_decoder import decode_barcode

# Decode from image
fields = decode_barcode('license_photo.jpg')

if fields:
    print(f"License Number: {fields['DAQ']}")
    print(f"Name: {fields['DAC']} {fields['DCS']}")
    print(f"Birth Date: {fields['DBB']}")
```

### Option 3: REST API

The Flask backend provides a REST API:

```bash
# Generate barcode (returns base64 image)
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "WDL123", "last_name": "SMITH", ...}'

# Download barcode as file
curl -X POST http://localhost:5000/api/download \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "WDL123", ...}' \
  -o barcode.png

# Get field information
curl http://localhost:5000/api/fields

# Health check
curl http://localhost:5000/api/health
```

## Technical Specifications

### PDF417 Configuration (Washington State)
- **Columns**: 13 configured → 15 visible data columns (verified from actual WA license)
- **Rows**: ~17 (auto-calculated based on data size)
- **Error Correction**: Level 5 (AAMVA standard)
- **Encoding**: UTF-8 compatible ASCII
- **Jurisdiction**: 636045 (Washington)
- **AAMVA Version**: 09 (2016 standard)

### AAMVA Data Elements

**Required:**
- `DAQ` - License Number
- `DCS` - Last Name  
- `DAC` - First Name
- `DBB` - Birth Date (MMDDYYYY)
- `DBC` - Sex (1=Male, 2=Female)
- `DAY` - Eye Color
- `DAU` - Height
- `DAG` - Street Address
- `DAI` - City
- `DAJ` - State
- `DAK` - Zip Code
- `DCG` - Country
- `DCF` - Document Discriminator
- `DBA` - Expiration Date
- `DBD` - Issue Date

**Optional:**
- `DAD` - Middle Name
- `DCA` - License Class
- `DCB` - Restrictions
- `DCD` - Endorsements
- `DAZ` - Hair Color
- `DCU` - Name Suffix
- `DAW` - Weight
- `DDA` - Compliance Type
- `DDB` - Revision Date
- `DDK` - Organ Donor

## Input Format Flexibility

**Dates** (accepts multiple formats):
- ISO: `1985-03-15`
- AAMVA: `03151985`
- Slash: `03/15/1985`

**Heights** (accepts multiple formats):
- Feet/inches: `5-10`, `5'10"`, `5ft 10in`
- Inches only: `70`, `70in`

## Testing

```bash
# Run all tests
python -m pytest test_aamva.py -v

# Quick verification
python -c "from aamva_pdf417 import create_wa_license_barcode; print('✅ Generator working')"
```

## Files

```
bcgen/
├── app.py                   # Flask web application
├── index.html              # Web interface
├── start.sh                 # Start script
├── aamva_pdf417.py         # AAMVA barcode generator
├── pdf417_encoder.py       # PDF417 encoding (15 columns)
├── pdf417_decoder.py       # PDF417 decoder (requires zxing-cpp)
├── test_aamva.py           # Comprehensive unit tests
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Web Application Features

🎨 **Modern UI:**
- Clean, responsive design
- Form-based data entry
- Real-time barcode preview
- Field validation

🚀 **Easy to Use:**
- No coding required
- Fill in the form
- Click generate
- Download instantly

🔧 **REST API:**
- Generate barcodes programmatically
- Integrate with other applications
- JSON-based communication

## How PDF417 Columns Work

**Important:** Columns are a layout parameter, not data organization.

- **15 columns** = How many codewords per row (physical layout)
- **NOT**: "Column 1 = license number, Column 2 = name, etc."
- Data flows sequentially through all codewords
- Decoder must read entire barcode to extract any field

Think of it like text on a page:
- Page width = 15 characters (columns)
- Text flows continuously across lines
- Can't say "character 5 = specific word"

## Verification Status

✅ **VERIFIED** against actual Washington State driver's license:
- Decoded real WA license barcode (313 bytes, 26 elements)
- Counted physical structure: 15 columns × 17 rows
- Confirmed jurisdiction code: 636045
- Confirmed AAMVA version: 09
- All tests passing (20/20)

## Notes

- For educational and legitimate use only
- Follows AAMVA DL/ID Card Design Standard Version 9 (2016)
- Column count verified from actual WA license barcode structure
- Generator produces AAMVA-compliant output

## AAMVA Data Format

The generator follows the AAMVA DL/ID Card Design Standard with this structure:

```
@                              # Compliance indicator
ANSI 636045090001DL           # Header (jurisdiction + version + subfiles)
DAQ[customer_id]              # Customer ID Number
DCS[last_name]                # Last Name
DAC[first_name]               # First Name
... (additional data elements)
```

### Mandatory Fields

| Field | Element ID | Description | Format |
|-------|-----------|-------------|--------|
| `customer_id` | DAQ | Driver's License Number | String |
| `last_name` | DCS | Last Name/Surname | String |
| `first_name` | DAC | First Name | String |
| `birth_date` | DBB | Date of Birth | MMDDYYYY |
| `expiration_date` | DBA | Expiration Date | MMDDYYYY |
| `sex` | DBC | Sex | 1=M, 2=F, 9=Other |
| `eye_color` | DAY | Eye Color | 3-letter code |
| `height` | DAU | Height | ###␣in (e.g., "070 in") |
| `address_street` | DAG | Street Address | String |
| `address_city` | DAI | City | String |
| `address_state` | DAJ | State | 2-letter code |
| `address_zip` | DAK | ZIP Code | String |
| `document_discriminator` | DCF | Document Discriminator | String |

### Optional Fields

| Field | Element ID | Description |
|-------|-----------|-------------|
| `middle_name` | DAD | Middle Name |
| `suffix` | DCU | Name Suffix (JR, SR, III) |
| `issue_date` | DBD | Issue Date |
| `hair_color` | DAZ | Hair Color (3-letter code) |
| `weight_pounds` | DAW | Weight in Pounds |
| `class` | DCA | License Class |
| `restrictions` | DCB | Restrictions Code |
| `endorsements` | DCD | Endorsements |
| `compliance_type` | DDA | Compliance Type |
| `under_21_until` | DDJ | Under 21 Until Date |
| `organ_donor` | DDK | Organ Donor (1=Yes, 0=No) |
| `veteran` | DDL | Veteran (1=Yes, 0=No) |

## Code Reference

### Eye Color Codes
```
BLK - Black    BLU - Blue     BRO - Brown
GRY - Gray     GRN - Green    HAZ - Hazel
MAR - Maroon   PNK - Pink     DIC - Dichromatic
UNK - Unknown
```

### Hair Color Codes
```
BAL - Bald     BLK - Black    BLN - Blond
BRO - Brown    GRY - Grey     RED - Red/Auburn
SDY - Sandy    WHI - White    UNK - Unknown
```

### Sex Codes
```
M - Male       F - Female     X - Non-binary/Other
U - Unknown
```

## Examples

Run the included examples:

```bash
python example.py
```

This will generate:
1. Standard adult Washington license barcode
2. Under-21 license barcode
3. Data validation demonstration

## Washington State Specifics

- **Jurisdiction Code**: 636045
- **AAMVA Version**: 09 (Version 9, 2016 standard)
- **Compliance Type**: F (Fully compliant with REAL ID)
- **Document Discriminator**: 20-digit unique identifier

## API Reference

### `AAMVAPDF417Generator`

Main class for generating barcode data.

```python
generator = AAMVAPDF417Generator()
barcode_data = generator.generate_barcode_data(license_data)
is_valid, errors = generator.validate_data(license_data)
```

### `PDF417Encoder`

Class for encoding barcode data to images.

```python
encoder = PDF417Encoder(security_level=5)
encoder.save_barcode(barcode_data, 'output.png', scale=3, ratio=3)
encoder.encode_to_svg(barcode_data, 'output.svg')
```

### Helper Functions

```python
# Create Washington license barcode (validates and generates)
barcode_data = create_wa_license_barcode(license_data)

# Generate barcode image
generate_barcode_image(barcode_data, 'output.png', format='PNG')

# Format utilities
formatted_date = AAMVADataFormatter.format_date('2024-03-15')
formatted_height = AAMVADataFormatter.format_height('5-10')
```

## Data Validation

The generator includes comprehensive validation:

```python
from aamva_pdf417 import AAMVAPDF417Generator

generator = AAMVAPDF417Generator()
is_valid, errors = generator.validate_data(license_data)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

## Date Format Support

The generator accepts multiple date formats:
- `YYYY-MM-DD` (e.g., "1985-03-15")
- `MM/DD/YYYY` (e.g., "03/15/1985")
- `MMDDYYYY` (e.g., "03151985")

All dates are automatically converted to AAMVA's `MMDDYYYY` format.

## Testing

```bash
# Run example tests
python example.py

# Test with pytest (if installed)
pytest test_aamva.py
```

## Security & Legal Notice

⚠️ **IMPORTANT**: This tool is for:
- Educational purposes
- Legitimate software development
- Testing and validation systems
- Authorized applications only

**DO NOT** use this to:
- Create fraudulent identification
- Forge driver's licenses
- Engage in any illegal activity

Creating fake identification documents is illegal and punishable by law.

## Technical Details

### PDF417 Specification
- **Columns**: 15 data columns (Washington State - verified from actual license)
- **Error Correction**: Level 5 (recommended for DL/ID cards)
- **Encoding**: UTF-8 compatible ASCII
- **Structure**: AAMVA compliance indicator + header + data elements
- **Note**: Column count is configurable per state requirements

### AAMVA Standard
- Based on AAMVA DL/ID Card Design Standard
- Version 9 (2016) implementation
- Supports backward compatibility with readers
- Follows ANSI/ISO standards

## Troubleshooting

### "pdf417 library not installed"
```bash
pip install pdf417
```

### "Pillow not installed"
```bash
pip install Pillow
```

### Date format errors
Ensure dates are in one of the supported formats:
- YYYY-MM-DD
- MM/DD/YYYY
- MMDDYYYY

### Barcode won't scan
- Ensure all required fields are provided
- Check that the image scale is sufficient (try scale=4)
- Verify the print quality and contrast
- Test with multiple barcode readers

## Contributing

Contributions are welcome! Please ensure:
1. Code follows PEP 8 style guidelines
2. All tests pass
3. Documentation is updated
4. Changes maintain AAMVA compliance

## References

- [AAMVA DL/ID Card Design Standard](https://www.aamva.org/)
- [PDF417 Barcode Standard](https://en.wikipedia.org/wiki/PDF417)
- [Washington State DOL](https://www.dol.wa.gov/)

## License

This project is provided as-is for educational and authorized use only. See security notice above.

## Changelog

### Version 1.0.0
- Initial release
- AAMVA Version 9 support
- Washington State configuration
- Full data validation
- Image generation support
- Comprehensive documentation

---

**Disclaimer**: This tool generates data structures compliant with AAMVA standards. It is intended for legitimate development and testing purposes only. Users are responsible for ensuring their use complies with all applicable laws and regulations.
