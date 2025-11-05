"""
AAMVA PDF417 Barcode Decoder
Decodes PDF417 barcodes from Washington State driver's licenses
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

import numpy as np
from typing import Dict, Optional


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
            img_array = np.array(img)
            
            # Decode barcodes
            results = zxingcpp.read_barcodes(img_array)
            
            # Find PDF417 barcode
            for result in results:
                if result.format == zxingcpp.BarcodeFormat.PDF417:
                    # Convert ZXing's literal control character representations
                    data = result.text
                    data = data.replace('<LF>', '\n')
                    data = data.replace('<CR>', '\r')
                    data = data.replace('<RS>', '\x1e')
                    return data
            
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
            Dictionary of element IDs to values
        """
        if not barcode_data:
            return {}
        
        lines = barcode_data.split('\n')
        elements = {}
        
        # Skip compliance indicator and header
        for line in lines[2:]:
            line_clean = line.strip('\r\x1e ')
            if len(line_clean) >= 3:
                elem_id = line_clean[:3]
                value = line_clean[3:]
                elements[elem_id] = value
        
        return elements
    
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
