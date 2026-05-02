"""
Invert Router — Invert all colors in a PDF (Dark Mode / Print Save)
Strategy: Render each page → invert pixel values → rebuild PDF
Useful for: eye comfort at night, saving printer ink (dark text on white → white on black)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import fitz
import numpy as np
import cv2
import io
from PIL import Image

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"


class InvertRequest(BaseModel):
    file_id: str
    dpi: int = 150          # render resolution — 150 is fast, 300 is crisp
    mode: str = "full"      # full | smart
    # full  = invert ALL colors (true complement)
    # smart = invert only dark areas (better for mixed content)


def invert_full(img_bgr: np.ndarray) -> np.ndarray:
    """True bitwise inversion — all colors flipped."""
    return cv2.bitwise_not(img_bgr)


def invert_smart(img_bgr: np.ndarray) -> np.ndarray:
    """
    Smart inversion: convert to grayscale awareness mode.
    Dark backgrounds → white; light text → dark.
    Colors are desaturated then inverted for legibility.
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2Lab)
    L, a, b = cv2.split(lab)

    # Invert only the L channel (luminance)
    L_inv = 255 - L

    # Reconstruct — reduce saturation of a,b channels toward neutral (128)
    a_neutral = (a.astype(np.int32) - 128) // 2 + 128
    b_neutral = (b.astype(np.int32) - 128) // 2 + 128

    lab_inv = cv2.merge([L_inv, a_neutral.astype(np.uint8), b_neutral.astype(np.uint8)])
    return cv2.cvtColor(lab_inv, cv2.COLOR_Lab2BGR)


@router.post("/invert")
async def invert_pdf(payload: InvertRequest):
    """Invert colors of all pages in the PDF."""
    src = UPLOAD_DIR / f"{payload.file_id}.pdf"
    if not src.exists():
        raise HTTPException(404, "Upload file nahi mila.")

    if payload.mode not in ("full", "smart"):
        raise HTTPException(400, "mode 'full' ya 'smart' hona chahiye.")

    dst = PROCESSED_DIR / f"{payload.file_id}.pdf"
    doc_in = fitz.open(str(src))
    doc_out = fitz.open()

    zoom = payload.dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    for page in doc_in:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")

        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            continue

        # Apply chosen inversion
        if payload.mode == "full":
            inverted = invert_full(img_bgr)
        else:
            inverted = invert_smart(img_bgr)

        # Rebuild page
        w_pt = page.rect.width
        h_pt = page.rect.height
        new_page = doc_out.new_page(width=w_pt, height=h_pt)

        inv_rgb = cv2.cvtColor(inverted, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(inv_rgb)
        img_io = io.BytesIO()
        pil_img.save(img_io, format="PNG")
        img_io.seek(0)
        new_page.insert_image(new_page.rect, stream=img_io.read())

    doc_out.save(str(dst), garbage=4, deflate=True)
    doc_out.close()
    doc_in.close()

    return {
        "file_id": payload.file_id,
        "mode": payload.mode,
        "pages_processed": len(doc_in),
        "message": f"PDF colors invert ho gayi ({payload.mode} mode). Dark/light switch complete!",
        "download_url": f"/api/download/{payload.file_id}",
    }
