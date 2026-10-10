"""
Flask Backend for AAMVA PDF417 Barcode Generator
Provides REST API for generating driver's license barcodes for all US states.

v2.0.0-alpha.1 — multi-jurisdiction: every state-specific decision (DL element
order, jurisdiction subfiles, PDF417 rows/columns, WA-only horizontal flip) is
resolved from the JurisdictionProfile registry in the `states` package.
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import io
import base64
from datetime import datetime
import os
import re

from aamva_pdf417 import create_license_barcode
from pdf417_encoder import PDF417Encoder
from states import get_profile, list_states, fields_as_dicts

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max


def normalize_license_data(data: dict) -> dict:
    """Normalize incoming data to meet AAMVA formatting expectations.

    State-agnostic: the jurisdiction is taken from data['state'] (falling back
    to address_state), and 'yes'/'no' UI values are mapped to AAMVA codes.
    """
    if not isinstance(data, dict):
        return {}

    # Resolve jurisdiction selector -> canonical state code
    state = (data.get('state') or data.get('address_state') or '').strip().upper()
    if state:
        data['state'] = state
        data['address_state'] = state

    # Map UI yes/no dropdowns to AAMVA element values
    compliance = str(data.get('compliance_type', '')).strip().upper()
    if compliance == 'YES':
        data['compliance_type'] = 'R'      # REAL ID compliant
    elif compliance in ('NO', ''):
        data['compliance_type'] = 'N'      # standard state license
    else:
        data['compliance_type'] = compliance  # raw code passthrough (R/E/B/F...)

    for bool_field in ('organ_donor', 'veteran'):
        if isinstance(data.get(bool_field), str) and data[bool_field].strip().lower() in ('yes', 'no'):
            data[bool_field] = 'YES' if data[bool_field].strip().lower() == 'yes' else 'NO'

    uppercase_fields = {
        'customer_id', 'last_name', 'first_name', 'middle_name', 'suffix',
        'address_street', 'address_city', 'address_state', 'document_discriminator',
        'eye_color', 'hair_color', 'class', 'restrictions', 'endorsements',
        'country_id', 'sex', 'jurisdiction_endorsement_code',
        'jurisdiction_endorsement_expiration', 'jurisdiction_restriction_code',
        'compliance_type', 'jurisdiction_version'
    }

    for field, value in list(data.items()):
        if isinstance(value, str):
            trimmed = value.strip()
            if field in uppercase_fields:
                trimmed = trimmed.upper()
            data[field] = trimmed

    # Normalize height (allow formats like 5'10" or 70)
    if isinstance(data.get('height'), str):
        height = data['height'].upper()
        height = height.replace('FEET', '').replace('FT', '').replace('INCHES', '').replace('IN', '')
        height = height.replace("'", '-').replace('"', '').replace(' ', '')
        if '-' in height:
            parts = [p for p in height.split('-') if p]
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                height = f"{int(parts[0])}-{int(parts[1])}"
        data['height'] = height

    # Normalize weight fields to digits only
    for weight_field in ('weight_pounds', 'weight'):
        if isinstance(data.get(weight_field), str):
            digits = re.sub(r'[^0-9]', '', data[weight_field])
            if digits:
                data[weight_field] = digits
            else:
                data.pop(weight_field, None)

    defaults = {
        'country_id': 'USA',
        'class': 'NONE',
        'restrictions': 'NONE',
        'endorsements': 'NONE',
        'compliance_type': 'N',
        'jurisdiction_endorsement_code': 'N',
        'jurisdiction_endorsement_expiration': 'N',
        'jurisdiction_restriction_code': 'N',
        'jurisdiction_version': '00'
    }

    for key, value in defaults.items():
        if not data.get(key):
            data[key] = value

    return data


@app.route('/')
def index():
    """Serve the main application page."""
    return send_from_directory('.', 'index.html')


@app.route('/api/states', methods=['GET'])
def api_states():
    """List every registered jurisdiction with its profile summary.

    Used by the UI state selector dropdown and status badges.
    """
    return jsonify({'states': list_states()})


@app.route('/api/generate', methods=['POST'])
def generate_barcode():
    """
    Generate a PDF417 barcode from provided license data.
    
    Request Body:
        JSON object with license data fields (must include 'state')
        
    Returns:
        JSON with barcode image (base64) or error message
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        data = normalize_license_data(dict(data))

        if not data.get('state'):
            return jsonify({'error': 'No state selected'}), 400

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
        
        # Resolve the jurisdiction profile (raises ValueError for unknown states)
        profile = get_profile(data['state'])

        # Generate barcode data (state-agnostic generator, profile-driven)
        barcode_data = create_license_barcode(data)
        
        # Encode to PDF417 image using this state's hardcoded geometry
        encoder = PDF417Encoder(config=profile.barcode)
        image = encoder.encode_to_image(
            barcode_data,
            width=profile.barcode.image_width,
            height=profile.barcode.image_height,
        )
        
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
            'state': profile.state,
            'barcode_config': {
                'columns': profile.barcode.columns,
                'rows': profile.barcode.rows,
                'security_level': profile.barcode.security_level,
                'flip_horizontal': profile.barcode.flip_horizontal,
            },
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

        data = normalize_license_data(dict(data))

        if not data.get('state'):
            return jsonify({'error': 'No state selected'}), 400

        profile = get_profile(data['state'])

        # Generate barcode data
        barcode_data = create_license_barcode(data)
        
        # Encode to PDF417 image using this state's hardcoded geometry
        encoder = PDF417Encoder(config=profile.barcode)
        image = encoder.encode_to_image(
            barcode_data,
            width=profile.barcode.image_width,
            height=profile.barcode.image_height,
        )
        
        # Save to buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Create filename from license number and timestamp
        license_num = data.get('customer_id', 'license')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{profile.state}_{license_num}_{timestamp}.png'
        
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

        data = normalize_license_data(dict(data))

        if not data.get('state'):
            return jsonify({'valid': False, 'error': 'No state selected'})
        
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
            barcode_data = create_license_barcode(data)
            return jsonify({
                'valid': True,
                'data_length': len(barcode_data),
                'state': data['state']
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

    Query Params:
        state (optional): two-letter code; when provided, the response is
        tailored to that jurisdiction's profile (IIN, subfiles, geometry).

    Returns:
        JSON with shared field schema plus per-state profile info.
    """
    state = (request.args.get('state') or '').strip().upper() or None
    payload = {'fields': fields_as_dicts()}

    if state:
        try:
            profile = get_profile(state)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        payload['profile'] = next(
            s for s in list_states() if s['state'] == profile.state
        )

    return jsonify(payload)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'AAMVA PDF417 Generator',
        'version': '2.0.0-alpha.1',
        'jurisdictions': len(list_states()),
        'configuration': {
            'generator': 'state-agnostic (profile-driven)',
            'researched_states': ['WA', 'MI'],
            'default_geometry': {'columns': 13, 'rows': None, 'security_level': 5},
            'aamva_version': '09'
        }
    })


if __name__ == '__main__':
    print("="*70)
    print("AAMVA PDF417 Barcode Generator - Web Service (v2.0.0-alpha.1)")
    print("="*70)
    print()
    print("Starting server...")
    print("Access the application at: http://localhost:5000")
    print()
    print("API Endpoints:")
    print("  GET  /                  - Web interface")
    print("  GET  /api/states        - List all jurisdictions + profiles")
    print("  POST /api/generate      - Generate barcode (returns base64 image)")
    print("  POST /api/download      - Generate and download barcode")
    print("  POST /api/validate      - Validate license data")
    print("  GET  /api/fields        - Get field schema (?state=XX)")
    print("  GET  /api/health        - Health check")
    print()
    print("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
