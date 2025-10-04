"""
PDF417 Barcode Encoder
Generates actual PDF417 barcode images from AAMVA data
"""

try:
    from pdf417 import encode, render_image
    PDF417_AVAILABLE = True
except ImportError:
    PDF417_AVAILABLE = False
    print("Warning: pdf417 library not installed. Install with: pip install pdf417")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL/Pillow not installed. Install with: pip install Pillow")


class PDF417Encoder:
    """
    Encodes AAMVA barcode data into PDF417 format and generates images.
    Configured for Washington State (13 columns configured = 15 visible data columns).
    """
    
    def __init__(self, security_level: int = 5, columns: int = 13):
        """
        Initialize the encoder.
        
        Args:
            security_level: Error correction level (0-8), default 5 for driver's licenses
            columns: Number of data columns (default 13 for WA - produces 15 visible columns)
        """
        if not PDF417_AVAILABLE:
            raise ImportError("pdf417 library is required. Install with: pip install pdf417")
        
        self.security_level = security_level
        self.columns = columns
    
    def encode_to_image(self, data: str, scale: int = 3, ratio: int = 3) -> Image:
        """
        Encode data to PDF417 barcode image.
        
        Args:
            data: The AAMVA-formatted barcode data string
            scale: Pixel scale factor (default 3)
            ratio: Height to width ratio of bars (default 3)
            
        Returns:
            PIL Image object containing the barcode
        """
        if not PIL_AVAILABLE:
            raise ImportError("Pillow library is required. Install with: pip install Pillow")
        
        # Encode the data to PDF417
        # Column count: AAMVA recommends 6-10 columns, but states vary widely
        # Washington State: configure 13 cols = 15 visible data columns (verified from actual)
        # More columns = wider but shorter barcode
        # Fewer columns = narrower but taller barcode
        codes = encode(data, 
                      columns=self.columns,  # WA: 13 configured = 15 visible
                      security_level=self.security_level)
        
        # Render to image
        image = render_image(codes, scale=scale, ratio=ratio, padding=10)
        
        return image
    
    def save_barcode(self, data: str, output_path: str, 
                     scale: int = 3, ratio: int = 3) -> None:
        """
        Generate and save PDF417 barcode to file.
        
        Args:
            data: The AAMVA-formatted barcode data string
            output_path: Path where to save the image
            scale: Pixel scale factor
            ratio: Height to width ratio of bars
        """
        image = self.encode_to_image(data, scale, ratio)
        image.save(output_path)
        print(f"Barcode saved to: {output_path}")
    
    def encode_to_svg(self, data: str, output_path: str) -> None:
        """
        Generate and save PDF417 barcode as SVG.
        
        Args:
            data: The AAMVA-formatted barcode data string
            output_path: Path where to save the SVG file
        """
        try:
            from pdf417 import render_svg
        except ImportError:
            raise ImportError("pdf417 SVG support not available")
        
        codes = encode(data, 
                      columns=self.columns,
                      security_level=self.security_level)
        
        svg_data = render_svg(codes, scale=3, ratio=3, padding=10)
        
        with open(output_path, 'w') as f:
            f.write(svg_data)
        
        print(f"SVG barcode saved to: {output_path}")


def generate_barcode_image(barcode_data: str, output_path: str, 
                          format: str = 'PNG') -> None:
    """
    Convenience function to generate barcode image.
    
    Args:
        barcode_data: AAMVA-formatted barcode data
        output_path: Where to save the image
        format: Output format ('PNG', 'SVG', 'JPEG')
    """
    encoder = PDF417Encoder()
    
    if format.upper() == 'SVG':
        encoder.encode_to_svg(barcode_data, output_path)
    else:
        encoder.save_barcode(barcode_data, output_path)


if __name__ == "__main__":
    # Test with sample data
    sample_data = """@
ANSI 636045090001DL00290191ZW02390013DLDCAD
DCSJOHN
DADDOE
DAQWD1234567
DBAD03152028
DBBD03151985
DCBD1
DAYBRO
DAU070 in
DCSSMITH
DCTJOHN
DAG123 MAIN ST
DAISEATTLE
DAJWA
DAK98101
DCFWE12345678901234567890"""
    
    if PDF417_AVAILABLE and PIL_AVAILABLE:
        try:
            encoder = PDF417Encoder()
            encoder.save_barcode(sample_data, "sample_license_barcode.png")
            print("\nSample barcode generated successfully!")
        except Exception as e:
            print(f"Error generating barcode: {e}")
    else:
        print("\nTo generate actual barcodes, install required libraries:")
        print("  pip install pdf417 Pillow")
