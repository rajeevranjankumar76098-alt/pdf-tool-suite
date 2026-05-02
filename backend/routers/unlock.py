"""
Unlock Router — Remove password from a PDF
Uses pypdf for decryption; falls back to qpdf CLI if available
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import subprocess
import shutil

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"


class UnlockRequest(BaseModel):
    file_id: str
    password: str


@router.post("/unlock")
async def unlock_pdf(payload: UnlockRequest):
    """Decrypt a password-protected PDF."""
    src = UPLOAD_DIR / f"{payload.file_id}.pdf"
    if not src.exists():
        raise HTTPException(404, "Upload file nahi mila.")

    dst = PROCESSED_DIR / f"{payload.file_id}.pdf"

    # ── Method 1: pypdf ───────────────────────────────────────────────────────
    reader = PdfReader(str(src))

    if not reader.is_encrypted:
        raise HTTPException(400, "Yeh PDF encrypted nahi hai — unlock ki zarurat nahi.")

    result = reader.decrypt(payload.password)
    if result == 0:
        # pypdf failed — try qpdf CLI if available
        if shutil.which("qpdf"):
            proc = subprocess.run(
                ["qpdf", "--password=" + payload.password, "--decrypt",
                 str(src), str(dst)],
                capture_output=True, text=True,
            )
            if proc.returncode != 0:
                raise HTTPException(403, "Password galat hai ya PDF unlock nahi ho sakta.")
            return {
                "file_id": payload.file_id,
                "message": "PDF unlock ho gaya! (qpdf engine)",
                "download_url": f"/api/download/{payload.file_id}",
            }
        raise HTTPException(403, "Password galat hai. Sahi password daalein.")

    # ── Write decrypted PDF ───────────────────────────────────────────────────
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    with open(dst, "wb") as f:
        writer.write(f)

    return {
        "file_id": payload.file_id,
        "message": "PDF unlock ho gaya! Ab bina password ke khul sakta hai.",
        "pages": len(reader.pages),
        "download_url": f"/api/download/{payload.file_id}",
    }
