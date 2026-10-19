"""Render the résumé PDF to images for the /resume/ page.

Usage:
    python tools/resume_to_png.py

Reads assets/justin-ren-liu-resume.pdf and writes one PNG per page,
assets/resume-1.png, assets/resume-2.png, ..., at about twice the page's
display width so it stays sharp on high-DPI screens. The page shows these
images (they look the same in every browser, phones included) and links the
PDF for downloading. Rerun this whenever the résumé PDF changes.

Needs PyMuPDF and Pillow: python -m pip install pymupdf pillow
"""
import glob
import os

import pymupdf
from PIL import Image

WIDTH = 1700   # px; the paper's text area is 780 px wide, so this is ~2x


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf = os.path.join(root, "assets", "justin-ren-liu-resume.pdf")
    for old in glob.glob(os.path.join(root, "assets", "resume-*.png")):
        os.remove(old)   # a shorter résumé shouldn't leave stale pages behind
    doc = pymupdf.open(pdf)
    for n, page in enumerate(doc, 1):
        zoom = WIDTH / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        out = os.path.join(root, "assets", f"resume-{n}.png")
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img.quantize(colors=64, dither=Image.Dither.NONE).save(out, optimize=True)   # text needs few colors: about half the size
        print(f"wrote assets/resume-{n}.png ({pix.width}x{pix.height})")


if __name__ == "__main__":
    main()
