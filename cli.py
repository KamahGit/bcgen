import argparse
import yaml
from aamva_pdf417 import create_wa_license_barcode

def main():
    parser = argparse.ArgumentParser(description="WA DL Barcode Generator CLI")
    parser.add_argument('--yaml', type=str, help='Path to YAML file with license data')
    parser.add_argument('--output', type=str, help='Output file for barcode data')
    parser.add_argument('--customer_id', type=str)
    parser.add_argument('--last_name', type=str)
    parser.add_argument('--first_name', type=str)
    parser.add_argument('--middle_name', type=str)
    parser.add_argument('--birth_date', type=str)
    parser.add_argument('--sex', type=str)
    parser.add_argument('--eye_color', type=str)
    parser.add_argument('--hair_color', type=str)
    parser.add_argument('--height', type=str)
    parser.add_argument('--weight', type=str)
    parser.add_argument('--address_street', type=str)
    parser.add_argument('--address_city', type=str)
    parser.add_argument('--address_state', type=str)
    parser.add_argument('--address_zip', type=str)
    parser.add_argument('--expiration_date', type=str)
    parser.add_argument('--issue_date', type=str)
    parser.add_argument('--document_discriminator', type=str)
    parser.add_argument('--class', type=str)
    parser.add_argument('--restrictions', type=str)
    parser.add_argument('--endorsements', type=str)
    parser.add_argument('--compliance_type', type=str)
    parser.add_argument('--organ_donor', action='store_true')
    parser.add_argument('--veteran', action='store_true')

    args = parser.parse_args()
    if args.yaml:
        with open(args.yaml, 'r') as f:
            data = yaml.safe_load(f)
    else:
        # Build data from args
        data = {k: v for k, v in vars(args).items() if v is not None and k not in ('output', 'yaml')}

    barcode_data = create_wa_license_barcode(data)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(barcode_data)
        print(f"Barcode data written to {args.output}")
    else:
        print(barcode_data)

if __name__ == '__main__':
    main()
