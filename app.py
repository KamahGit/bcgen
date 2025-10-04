"""
Flask Backend for AAMVA PDF417 Barcode Generator
Provides REST API for generating Washington State driver's license barcodes
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import io
import base64
from datetime import datetime
import os

from aamva_pdf417 import create_wa_license_barcode
from pdf417_encoder import PDF417Encoder

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max


@app.route('/')
def index():
    """Serve the main application page."""
    return send_from_directory('.', 'index.html')


@app.route('/api/generate', methods=['POST'])
def generate_barcode():
    """
    Generate a PDF417 barcode from provided license data.
    
    Request Body:
        JSON object with license data fields
        
    Returns:
        JSON with barcode image (base64) or error message
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = [
            'customer_id', 'last_name', 'first_name', 'birth_date',
            'sex', 'eye_color', 'height', 'address_street', 'address_city',
            'address_state', 'address_zip', 'expiration_date', 'issue_date',
            'document_discriminator'
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields
            }), 400
        
        # Generate barcode data
        barcode_data = create_wa_license_barcode(data)
        
        # Encode to PDF417 image
        encoder = PDF417Encoder()
        image = encoder.encode_to_image(barcode_data)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Convert to base64 for JSON response
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'data_length': len(barcode_data),
            'generated_at': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500


@app.route('/api/download', methods=['POST'])
def download_barcode():
    """
    Generate and download a PDF417 barcode as PNG file.
    
    Request Body:
        JSON object with license data fields
        
    Returns:
        PNG image file for download
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Generate barcode data
        barcode_data = create_wa_license_barcode(data)
        
        # Encode to PDF417 image
        encoder = PDF417Encoder()
        image = encoder.encode_to_image(barcode_data)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Create filename from license number and timestamp
        license_num = data.get('customer_id', 'license')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{license_num}_{timestamp}.png'
        
        return send_file(
            img_buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=filename
        )
        
    except ValueError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500


@app.route('/api/validate', methods=['POST'])
def validate_data():
    """
    Validate license data without generating barcode.
    
    Request Body:
        JSON object with license data fields
        
    Returns:
        JSON with validation results
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Required fields
        required_fields = [
            'customer_id', 'last_name', 'first_name', 'birth_date',
            'sex', 'eye_color', 'height', 'address_street', 'address_city',
            'address_state', 'address_zip', 'expiration_date', 'issue_date',
            'document_discriminator'
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'valid': False,
                'missing_fields': missing_fields
            })
        
        # Try to generate (validates format)
        try:
            barcode_data = create_wa_license_barcode(data)
            return jsonify({
                'valid': True,
                'data_length': len(barcode_data)
            })
        except ValueError as e:
            return jsonify({
                'valid': False,
                'error': str(e)
            })
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


@app.route('/api/fields', methods=['GET'])
def get_field_info():
    """
    Get information about available AAMVA fields.
    
    Returns:
        JSON with field definitions and examples
    """
    fields = {
        'required': {
            'customer_id': {
                'label': 'License Number',
                'example': 'WDL123456789',
                'description': 'Unique driver license number'
            },
            'last_name': {
                'label': 'Last Name',
                'example': 'SMITH',
                'description': 'Family name (uppercase)'
            },
            'first_name': {
                'label': 'First Name',
                'example': 'JOHN',
                'description': 'Given name (uppercase)'
            },
            'birth_date': {
                'label': 'Birth Date',
                'example': '1985-03-15',
                'description': 'Date of birth (YYYY-MM-DD)'
            },
            'sex': {
                'label': 'Sex',
                'example': 'M',
                'description': 'M (Male) or F (Female)'
            },
            'eye_color': {
                'label': 'Eye Color',
                'example': 'BRO',
                'description': 'BLK, BLU, BRO, GRY, GRN, HAZ, etc.'
            },
            'height': {
                'label': 'Height',
                'example': '5-10',
                'description': "Feet-inches (5-10) or inches (70)"
            },
            'address_street': {
                'label': 'Street Address',
                'example': '123 MAIN ST',
                'description': 'Street address'
            },
            'address_city': {
                'label': 'City',
                'example': 'SEATTLE',
                'description': 'City name'
            },
            'address_state': {
                'label': 'State',
                'example': 'WA',
                'description': 'Two-letter state code'
            },
            'address_zip': {
                'label': 'ZIP Code',
                'example': '98101',
                'description': '5-digit ZIP code'
            },
            'expiration_date': {
                'label': 'Expiration Date',
                'example': '2028-03-15',
                'description': 'License expiration (YYYY-MM-DD)'
            },
            'issue_date': {
                'label': 'Issue Date',
                'example': '2024-03-15',
                'description': 'License issue date (YYYY-MM-DD)'
            },
            'document_discriminator': {
                'label': 'Document Discriminator',
                'example': '12345678901234567890',
                'description': 'Unique document identifier'
            }
        },
        'optional': {
            'middle_name': {
                'label': 'Middle Name',
                'example': 'ROBERT',
                'description': 'Middle name or initial'
            },
            'class': {
                'label': 'License Class',
                'example': 'C',
                'description': 'License class (A, B, C, etc.)'
            },
            'restrictions': {
                'label': 'Restrictions',
                'example': 'B',
                'description': 'Restriction codes'
            },
            'endorsements': {
                'label': 'Endorsements',
                'example': 'NONE',
                'description': 'Endorsement codes'
            },
            'hair_color': {
                'label': 'Hair Color',
                'example': 'BRO',
                'description': 'Hair color code'
            },
            'weight': {
                'label': 'Weight',
                'example': '180',
                'description': 'Weight in pounds'
            }
        }
    }
    
    return jsonify(fields)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'AAMVA PDF417 Generator',
        'version': '1.0.0',
        'configuration': {
            'columns': 13,  # configured (produces 15 visible data columns)
            'visible_columns': 15,  # actual visible data columns
            'error_correction': 5,
            'jurisdiction': '636045',
            'aamva_version': '09'
        }
    })


if __name__ == '__main__':
    print("="*70)
    print("AAMVA PDF417 Barcode Generator - Web Service")
    print("="*70)
    print()
    print("Starting server...")
    print("Access the application at: http://localhost:5000")
    print()
    print("API Endpoints:")
    print("  GET  /                  - Web interface")
    print("  POST /api/generate      - Generate barcode (returns base64 image)")
    print("  POST /api/download      - Generate and download barcode")
    print("  POST /api/validate      - Validate license data")
    print("  GET  /api/fields        - Get field information")
    print("  GET  /api/health        - Health check")
    print()
    print("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
