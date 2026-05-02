"""
Compress Router — PDF file size reduction
Strategy: PyMuPDF garbage collection + deflate + image downsampling
Optional: Ghostscript for aggressive compression
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import fitz
import subprocess
import shutil
import os

router = APIRouter()

# Folder Paths - Updated to match your 'outputs' folder
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"  # Changed from 'processed' to 'outputs'

class CompressRequest(BaseModel):
    file_id: str
    quality: str = "medium"  # low | medium | high

GHOSTSCRIPT_SETTINGS = {
    "low":    "/screen",   # 72 dpi images
    "medium": "/ebook",    # 150 dpi images
    "high":   "/printer",  # 300 dpi images
}

def gs_available() -> bool:
    """Checks if Ghostscript is installed on the system."""
    return shutil.which("gs") is not None or shutil.which("gswin64c") is not None

def compress_with_gs(src: Path, dst: Path, quality: str):
    """Aggressive compression using Ghostscript."""
    gs_cmd = "gswin64c" if shutil.which("gswin64c") else "gs"
    setting = GHOSTSCRIPT_SETTINGS.get(quality, "/ebook")
    result = subprocess.run(
        [
            gs_cmd,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={setting}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={str(dst)}",
            str(src),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript error: {result.stderr}")

def compress_with_pymupdf(src: Path, dst: Path, quality: str):
    """Fallback: High-quality compression using PyMuPDF."""
    doc = fitz.open(str(src))

    # Downsampling images to reduce size
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            
            # Convert to RGB if necessary
            if pix.n >= 5:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            
            if quality == "low":
                new_pix = pix.shrink(2) # Half resolution
                doc.update_stream(xref, new_pix.tobytes("jpg", jpg_quality=40))
            elif quality == "medium":
                doc.update_stream(xref, pix.tobytes("jpg", jpg_quality=70))

    # Save with garbage collection and compression flags
    doc.save(
        str(dst),
        garbage=4,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        clean=True,
    )
    doc.close()

@router.post("/compress")
async def compress_pdf(payload: CompressRequest):
    # 1. Path Setup & Verification
    src = UPLOAD_DIR / f"{payload.file_id}.pdf"
    dst = OUTPUT_DIR / f"{payload.file_id}.pdf"

    if not src.exists():
        raise HTTPException(404, "Upload file nahi mila. Dobara upload karein.")

    # 2. Ensure Output Directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    original_size = src.stat().st_size

    try:
        # 3. Compression Execution
        if gs_available():
            compress_with_gs(src, dst, payload.quality)
            engine = "ghostscript"
        else:
            compress_with_pymupdf(src, dst, payload.quality)
            engine = "pymupdf"

        # 4. Result Calculation
        new_size = dst.stat().st_size
        reduction = round((1 - new_size / original_size) * 100, 1)

        return {
            "file_id": payload.file_id,
            "original_size_kb": original_size // 1024,
            "compressed_size_kb": new_size // 1024,
            "reduction_percent": reduction,
            "engine": engine,
            "message": f"PDF compress ho gaya! {reduction}% size kam hua.",
            "download_url": f"/api/download/{payload.file_id}",
        }

    except Exception as e:
        # Log the error for the developer
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(500, f"Compression process mein error: {str(e)}")