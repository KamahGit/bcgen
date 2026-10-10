"""
PDF417 Barcode Encoder
Generates actual PDF417 barcode images from AAMVA data
"""

from typing import Optional
from xml.etree.ElementTree import tostring

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
    Geometry (columns/rows/security level) and the Washington-only horizontal
    flip are supplied per jurisdiction via a BarcodeConfig or explicit args —
    nothing state-specific is baked in.
    """

    def __init__(self, security_level: Optional[int] = None,
                 columns: Optional[int] = None,
                 rows: Optional[int] = None,
                 flip_horizontal: Optional[bool] = None,
                 config=None):
        """
        Initialize the encoder.

        Args:
            security_level: Error correction level (0-8); from config if omitted
            columns: Number of data columns; from config if omitted
            rows: Expected row count (documentation/verification only — the
                  pdf417 library derives rows from columns + data length)
            flip_horizontal: Horizontally flip rendered image (Washington only)
            config: states.BarcodeConfig instance — explicit args override it
        """
        if not PDF417_AVAILABLE:
            raise ImportError("pdf417 library is required. Install with: pip install pdf417")

        self.security_level = (security_level if security_level is not None
                               else (config.security_level if config else 5))
        self.columns = (columns if columns is not None
                        else (config.columns if config else 13))
        self.rows = rows if rows is not None else (config.rows if config else None)
        self.flip_horizontal = (flip_horizontal if flip_horizontal is not None
                                else (config.flip_horizontal if config else False))
    
    def encode_to_image(self, data: str, scale: int = 3, ratio: int = 3, width: int = None, height: int = None) -> Image:
        """
        Encode data to PDF417 barcode image.
        
        Args:
            data: The AAMVA-formatted barcode data string
            scale: Pixel scale factor (default 3)
            ratio: Height to width ratio of bars (default 3)
            width: Target width in pixels. If provided, image is resized.
            height: Target height in pixels. If provided, image is resized.
            
        Returns:
            PIL Image object containing the barcode
        """
        if not PIL_AVAILABLE:
            raise ImportError("Pillow library is required. Install with: pip install Pillow")
        
        # Encode the data to PDF417 (per-state geometry from profile config).
        # NOTE: the pdf417 PyPI package's encode() only accepts columns and
        # security_level — row count falls out of column count + data length.
        # The profile's rows hint is therefore not passed to the encoder; it is
        # kept on BarcodeConfig for documentation/verification only.
        codes = encode(data, columns=self.columns, security_level=self.security_level)

        # Render to image
        image = render_image(codes, scale=scale, ratio=ratio, padding=10)

        # Resize image if width and height are provided
        if width and height:
            try:
                # For Pillow >= 9.1.0
                from PIL.Image import Resampling
                image = image.resize((width, height), Resampling.LANCZOS)
            except ImportError:
                # For older Pillow
                image = image.resize((width, height), Image.LANCZOS)
        
        # Horizontal flip is jurisdiction-specific (Washington does it;
        # other states do not).  Driven by BarcodeConfig.flip_horizontal.
        if self.flip_horizontal:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        return image
    
    def save_barcode(self, data: str, output_path: str, 
                     scale: int = 3, ratio: int = 3, width: int = None, height: int = None) -> None:
        """
        Generate and save PDF417 barcode to file.
        
        Args:
            data: The AAMVA-formatted barcode data string
            output_path: Path where to save the image
            scale: Pixel scale factor
            ratio: Height to width ratio of bars
            width: Target width in pixels.
            height: Target height in pixels.
        """
        image = self.encode_to_image(data, scale, ratio, width, height)
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
        
        # pdf417.encode() supports columns/security_level only; rows is a
        # documentation hint kept on the profile, never passed to the encoder.
        codes = encode(data, columns=self.columns, security_level=self.security_level)

        # render_svg() does not accept a padding kwarg (unlike render_image)
        # and returns an xml.etree ElementTree, not a string.
        svg_tree = render_svg(codes, scale=3, ratio=3)
        if isinstance(svg_tree, str):
            svg_data = svg_tree.encode('utf-8')
        else:
            root = svg_tree.getroot() if hasattr(svg_tree, 'getroot') else svg_tree
            svg_data = tostring(root, encoding='unicode').encode('utf-8')

        with open(output_path, 'wb') as f:
            f.write(svg_data)
        
        print(f"SVG barcode saved to: {output_path}")


def encoder_for_state(state: str) -> "PDF417Encoder":
    """Build an encoder pre-configured with a jurisdiction's barcode geometry."""
    from states import get_profile
    profile = get_profile(state)
    return PDF417Encoder(config=profile.barcode)


def generate_barcode_image(barcode_data: str, output_path: str,
                          format: str = 'PNG', state: Optional[str] = None) -> None:
    """
    Convenience function to generate barcode image.

    Args:
        barcode_data: AAMVA-formatted barcode data
        output_path: Where to save the image
        format: Output format ('PNG', 'SVG', 'JPEG')
        state: Jurisdiction whose hardcoded PDF417 geometry should be used
    """
    encoder = encoder_for_state(state) if state else PDF417Encoder()
    
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
