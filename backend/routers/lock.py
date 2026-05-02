"""
Lock Router — Add password protection to a PDF
Uses pypdf for standard AES-128 / RC4 encryption
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from pypdf import PdfReader, PdfWriter

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"


class LockRequest(BaseModel):
    file_id: str
    user_password: str          # password to open the PDF
    owner_password: str = ""    # password for full permissions (optional; defaults to user_password)
    allow_printing: bool = True
    allow_copying: bool = False


@router.post("/lock")
async def lock_pdf(payload: LockRequest):
    """Encrypt PDF with user + owner passwords."""
    src = UPLOAD_DIR / f"{payload.file_id}.pdf"
    if not src.exists():
        raise HTTPException(404, "Upload file nahi mila.")

    if len(payload.user_password) < 4:
        raise HTTPException(400, "Password kam se kam 4 characters ka hona chahiye.")

    dst = PROCESSED_DIR / f"{payload.file_id}.pdf"

    reader = PdfReader(str(src))
    if reader.is_encrypted:
        raise HTTPException(400, "Yeh PDF pehle se encrypted hai. Pehle unlock karein.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    owner_pw = payload.owner_password or payload.user_password

    writer.encrypt(
        user_password=payload.user_password,
        owner_password=owner_pw,
        use_128bit=True,
    )

    with open(dst, "wb") as f:
        writer.write(f)

    return {
        "file_id": payload.file_id,
        "message": f"PDF lock ho gaya! Password: '{payload.user_password}'",
        "pages": len(reader.pages),
        "download_url": f"/api/download/{payload.file_id}",
    }
