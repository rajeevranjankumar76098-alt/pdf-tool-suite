"""
Edit Router — Add text/annotations to any PDF page
Uses PyMuPDF (fitz) for precise text placement
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import fitz  # PyMuPDF

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"


class TextEdit(BaseModel):
    file_id: str
    page_number: int = 0          # 0-indexed
    text: str
    x: float = 50.0               # position from left
    y: float = 50.0               # position from top
    font_size: float = 14.0
    font_color: str = "#000000"   # hex color
    font_name: str = "helv"       # helv / times / cour / zadb
    bold: bool = False
    italic: bool = False


def hex_to_rgb(hex_color: str) -> tuple:
    """#RRGGBB → (r, g, b) float 0-1"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (r / 255, g / 255, b / 255)


@router.post("/edit")
async def edit_pdf(payload: TextEdit):
    """Add text overlay to a specific page of the PDF."""
    src = UPLOAD_DIR / f"{payload.file_id}.pdf"
    if not src.exists():
        raise HTTPException(404, "Upload file nahi mila. Pehle /api/upload karein.")

    dst = PROCESSED_DIR / f"{payload.file_id}.pdf"
    doc = fitz.open(str(src))

    if payload.page_number >= len(doc):
        raise HTTPException(400, f"Page {payload.page_number} exist nahi karta. PDF mein {len(doc)} pages hain.")

    page = doc[payload.page_number]
    color = hex_to_rgb(payload.font_color)

    # Build fontname with bold/italic flags
    font = payload.font_name
    if payload.bold and payload.italic:
        font = font + "-BoldOblique"
    elif payload.bold:
        font = font + "-Bold"
    elif payload.italic:
        font = font + "-Oblique"

    # Insert text
    page.insert_text(
        point=fitz.Point(payload.x, payload.y),
        text=payload.text,
        fontsize=payload.font_size,
        fontname=font,
        color=color,
    )

    doc.save(str(dst), garbage=4, deflate=True)
    doc.close()

    return {
        "file_id": payload.file_id,
        "message": f"Text '{payload.text}' page {payload.page_number + 1} pe add ho gaya",
        "download_url": f"/api/download/{payload.file_id}",
    }
