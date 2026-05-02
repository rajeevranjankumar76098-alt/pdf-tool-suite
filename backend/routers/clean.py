"""
Clean Router — Remove Handwriting / Pen Marks from PDF
Strategy:
  1. Render each page to high-res image (PyMuPDF)
  2. Detect ink strokes via color thresholding (OpenCV)
     — Pen marks are typically dark on light background
     — We inpaint those regions using surrounding pixels
  3. Reassemble cleaned pages into a new PDF (img2pdf / reportlab)

Works best on scanned PDFs with clear handwriting on white background.
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


class CleanRequest(BaseModel):
    file_id: str
    dpi: int = 200                  # render resolution (150-300 recommended)
    ink_threshold: int = 150        # 0-255; pixels darker than this = possible ink
    min_area: int = 30              # ignore very small specks
    inpaint_radius: int = 7         # larger = smoother fill
    preserve_printed_text: bool = True  # try to keep black typeset text


def remove_handwriting(img_bgr: np.ndarray, threshold: int, min_area: int,
                        inpaint_radius: int, preserve_printed: bool) -> np.ndarray:
    """Core pen-mark removal using OpenCV."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # --- Step 1: find all dark regions (ink candidates) ---
    _, dark_mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    if preserve_printed:
        # Heuristic: printed text has very uniform, straight edges (high solidity).
        # Handwriting tends to be more irregular.
        # We use connected component analysis to classify each blob.
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(dark_mask, 8)
        handwriting_mask = np.zeros_like(dark_mask)

        for i in range(1, num_labels):  # skip background (label 0)
            area = stats[i, cv2.CC_STAT_AREA]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]

            if area < min_area:
                continue  # too small, ignore

            aspect = max(w, h) / (min(w, h) + 1)
            solidity = area / (w * h + 1)

            # Pen strokes: elongated (high aspect) OR low solidity (irregular)
            # Printed text chars: compact, high solidity
            if aspect > 5 or solidity < 0.25 or (area > 2000 and aspect > 2):
                handwriting_mask[labels == i] = 255
    else:
        handwriting_mask = dark_mask

    # --- Step 2: dilate to cover stroke edges fully ---
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    handwriting_mask = cv2.dilate(handwriting_mask, kernel, iterations=2)

    # --- Step 3: inpaint (Navier-Stokes) ---
    cleaned = cv2.inpaint(img_bgr, handwriting_mask, inpaint_radius, cv2.INPAINT_NS)
    return cleaned


@router.post("/clean")
async def clean_pdf(payload: CleanRequest):
    """Remove pen/handwriting marks from each page of the PDF."""
    src = UPLOAD_DIR / f"{payload.file_id}.pdf"
    if not src.exists():
        raise HTTPException(404, "Upload file nahi mila.")

    dst = PROCESSED_DIR / f"{payload.file_id}.pdf"
    doc_in = fitz.open(str(src))
    doc_out = fitz.open()

    zoom = payload.dpi / 72  # default PDF DPI is 72
    mat = fitz.Matrix(zoom, zoom)

    for page_num, page in enumerate(doc_in):
        # Render page to image
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")

        # Convert to OpenCV array
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            continue  # skip unreadable page

        # Remove handwriting
        cleaned_bgr = remove_handwriting(
            img_bgr,
            threshold=payload.ink_threshold,
            min_area=payload.min_area,
            inpaint_radius=payload.inpaint_radius,
            preserve_printed=payload.preserve_printed_text,
        )

        # Convert back to PNG bytes
        _, cleaned_bytes = cv2.imencode(".png", cleaned_bgr)
        cleaned_pil = Image.frombytes("RGB", (pix.width, pix.height),
                                       cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB))

        # Insert cleaned image as a new PDF page (same size as original)
        w_pt = page.rect.width
        h_pt = page.rect.height
        new_page = doc_out.new_page(width=w_pt, height=h_pt)

        # Convert PIL → bytes → insert into page
        img_io = io.BytesIO()
        cleaned_pil.save(img_io, format="PNG")
        img_io.seek(0)
        new_page.insert_image(new_page.rect, stream=img_io.read())

    doc_out.save(str(dst), garbage=4, deflate=True)
    doc_out.close()
    doc_in.close()

    return {
        "file_id": payload.file_id,
        "pages_processed": len(doc_in),
        "message": "Handwriting/pen marks remove ho gayi. PDF clean ho gaya!",
        "download_url": f"/api/download/{payload.file_id}",
    }
