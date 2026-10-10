"""
AAMVA PDF417 Barcode Decoder
Decodes PDF417 barcodes from any supported US state driver's license.

The ANSI header supplies the jurisdiction IIN which is resolved back to a
state via the registry; subfiles (DL, ZM, ZW, ...) are split on carriage
returns and their elements on line feeds.  Barcodes generated for WA are
stored horizontally flipped, so decoding tries both orientations.
"""

try:
    import zxingcpp
    ZXING_AVAILABLE = True
except ImportError:
    ZXING_AVAILABLE = False
    print("Warning: zxing-cpp not installed. Install with: pip install zxing-cpp")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL/Pillow not installed. Install with: pip install Pillow")

import re
import numpy as np
from typing import Dict, Optional

from states.registry import iin_to_state


class PDF417Decoder:
    """Decode PDF417 barcodes from images."""
    
    def decode_from_image(self, image_path: str) -> Optional[str]:
        """
        Decode PDF417 barcode from an image file.
        
        Args:
            image_path: Path to image file containing PDF417 barcode
            
        Returns:
            Decoded barcode data as string, or None if decoding failed
        """
        if not ZXING_AVAILABLE:
            raise ImportError("zxing-cpp library required. Install with: pip install zxing-cpp")
        
        if not PIL_AVAILABLE:
            raise ImportError("Pillow library required. Install with: pip install Pillow")
        
        try:
            # Load image
            img = Image.open(image_path)

            # Some jurisdictions (Washington) store the rendered barcode
            # horizontally flipped; try normal then mirrored orientation.
            for attempt, candidate in enumerate((img, img.transpose(Image.FLIP_LEFT_RIGHT))):
                img_array = np.array(candidate)
                results = zxingcpp.read_barcodes(img_array)

                for result in results:
                    if result.format == zxingcpp.BarcodeFormat.PDF417:
                        # Convert ZXing's literal control character representations
                        data = result.text
                        data = data.replace('<LF>', '\n')
                        data = data.replace('<CR>', '\r')
                        data = data.replace('<RS>', '\x1e')
                        return data
                if attempt == 0 and not results:
                    continue
            return None
            
        except Exception as e:
            print(f"Error decoding barcode: {e}")
            return None
    
    def parse_aamva_data(self, barcode_data: str) -> Dict[str, str]:
        """
        Parse AAMVA-formatted barcode data into fields.

        Args:
            barcode_data: Raw barcode data string

        Returns:
            Dictionary of element IDs to values.  Jurisdiction-specific
            subfile elements (ZMA, ZMB, ...) appear alongside DL elements.
        """
        parsed = self.parse_aamva(barcode_data)
        return parsed.get("elements", {})

    @staticmethod
    def parse_aamva(barcode_data: str) -> Dict:
        """
        Full structural parse: header metadata + per-subfile elements.

        Returns dict with keys:
          iin, state, aamva_version, jurisdiction_version, num_subfiles,
          subfiles: [{"type_id","offset","length"}, ...],
          elements: {element_id: value}
        """
        info: Dict = {"elements": {}, "subfiles": []}
        if not barcode_data:
            return info

        # Locate the ANSI header line
        m = re.search(r"ANSI (\d{6})(\d{2})(\d{2})(\d{2})", barcode_data)
        if m:
            info["iin"] = m.group(1)
            info["aamva_version"] = m.group(2)
            info["jurisdiction_version"] = m.group(3)
            info["num_subfiles"] = int(m.group(4))
            info["state"] = iin_to_state(m.group(1))

            # Subfile descriptors: <TYPE><offset:4><len:4>, repeated
            pos = m.end()
            n = info["num_subfiles"] or 1
            for _ in range(n):
                dm = re.match(r"([A-Z]{2})(\d{4})(\d{4})", barcode_data[pos:pos + 10])
                if not dm:
                    break
                info["subfiles"].append({
                    "type_id": dm.group(1),
                    "offset": int(dm.group(2)),
                    "length": int(dm.group(3)),
                })
                pos += 10

        # Body: after the compliance indicator ("@\n\x1e").  Split subfiles on
        # CR, elements within each subfile on LF.
        body_start = barcode_data.find("\x1e")
        if body_start == -1:
            return info
        body = barcode_data[body_start + 1:]

        for chunk in body.split("\r"):
            chunk = chunk.strip()
            if not chunk:
                continue
            tokens = chunk.split("\n")
            pending_prefix = None    # 2-letter id split onto its own line
            for token in tokens:
                token = token.strip()
                if len(token) < 2:
                    continue
                if len(token) == 2 and token.isalpha():
                    # Subfile type id (DL/ZM/...) or a bare element prefix
                    # whose value was emitted empty (e.g. 'DA' + 'H').
                    pending_prefix = token
                    continue
                # Recombine a split id: prefix line + next line starting with
                # the missing letter(s), e.g. "DA" then "H..." -> "DAH..."
                if pending_prefix and len(token) >= 3 and \
                        token.startswith(pending_prefix[-1:]) and \
                        (pending_prefix + token[:2]).startswith(("DA", "DC", "DD", "Z")):
                    joined = pending_prefix + token
                    elem_id, value = joined[:3], joined[3:]
                    pending_prefix = None
                else:
                    elem_id, value = token[:3], token[3:]
                    if elem_id == "DL" and value.startswith("DL"):
                        value = value[2:]     # 'DL' type id glued to first element
                    pending_prefix = None
                if elem_id == "ANS":          # header line safety net
                    continue
                info["elements"][elem_id] = value
        return info
    
    def decode_and_parse(self, image_path: str) -> Optional[Dict[str, str]]:
        """
        Decode barcode from image and parse into fields.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary of parsed fields, or None if decoding failed
        """
        data = self.decode_from_image(image_path)
        print("raw data:", repr(data))
        if data:
            return self.parse_aamva_data(data)
        return None


def decode_barcode(image_path: str) -> Optional[Dict[str, str]]:
    """
    Convenience function to decode and parse a barcode image.
    
    Args:
        image_path: Path to image file containing PDF417 barcode
        
    Returns:
        Dictionary of parsed AAMVA fields
        
    Example:
        >>> fields = decode_barcode('license.jpg')
        >>> print(fields['DAQ'])  # License number
        >>> print(fields['DCS'])  # Last name
    """
    decoder = PDF417Decoder()
    return decoder.decode_and_parse(image_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf417_decoder.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"Decoding barcode from: {image_path}")
    print()
    
    fields = decode_barcode(image_path)
    print('raw fields:', fields)
    if fields:
        print("Successfully decoded!")
        print()
        print("AAMVA Fields:")
        print("-" * 70)
        for elem_id in sorted(fields.keys()):
            value = fields[elem_id]
            display = value[:60] + "..." if len(value) > 60 else value
            print(f"  {elem_id}: {display}")
    else:
        print("Failed to decode barcode from image")
