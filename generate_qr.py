#!/usr/bin/env python
"""Generate QR code for Streamlit app URL."""

import sys
import qrcode
from pathlib import Path

def generate_qr(url: str, output_file: str = "qr_code.png"):
    """Generate QR code for the given URL."""
    print(f"🔗 Generando QR para: {url}")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_file)

    print(f"✅ QR code guardado en: {output_file}")
    print(f"📐 Tamaño: {img.size[0]}x{img.size[1]} píxeles")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_qr.py <URL>")
        print("Ejemplo: python generate_qr.py https://citecrawl-demo.streamlit.app")
        sys.exit(1)

    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "qr_code.png"

    generate_qr(url, output_file)
