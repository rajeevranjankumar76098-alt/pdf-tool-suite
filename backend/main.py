"""
PDF Tool Suite - Backend API (100% Offline)
FastAPI server - localhost:8000
Updated: May 2026
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import uuid
import shutil
from pathlib import Path

# Routers import - Ensure these files exist in your 'routers' folder
from routers import edit, compress, clean, invert, lock, unlock

# ── Directory setup ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
# Fixed: Changing 'processed' to 'outputs' to match the system
PROCESSED_DIR = BASE_DIR / "outputs" 

# Create folders if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 PDF Tool Suite backend started — localhost:8000")
    yield
    print("👋 Server shutting down")

# ── App Initialization ───────────────────────────────────────────────────────
app = FastAPI(
    title="PDF Tool Suite",
    description="Offline PDF editing, compression, and security tools",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Frontend (React/Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include All Routers ──────────────────────────────────────────────────────
app.include_router(edit.router,     prefix="/api", tags=["Edit"])
app.include_router(compress.router, prefix="/api", tags=["Compress"])
app.include_router(clean.router,    prefix="/api", tags=["Clean"])
app.include_router(invert.router,   prefix="/api", tags=["Invert"])
app.include_router(lock.router,     prefix="/api", tags=["Lock"])
app.include_router(unlock.router,   prefix="/api", tags=["Unlock"])

# ── Shared Upload Endpoint ───────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF and receive a unique file_id."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sirf PDF files allowed hain")

    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}.pdf"

    # Save file to uploads folder
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size_kb = save_path.stat().st_size // 1024
    return {
        "file_id": file_id,
        "original_name": file.filename,
        "size_kb": size_kb,
        "message": "File successfully upload hua",
    }

# ── Shared Download Endpoint ─────────────────────────────────────────────────
@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    """Download a processed PDF from the outputs folder."""
    path = PROCESSED_DIR / f"{file_id}.pdf"
    
    if not path.exists():
        # Debugging log for terminal
        print(f"❌ Download Error: File not found at {path}")
        raise HTTPException(status_code=404, detail="Processed file nahi mila")
        
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"processed_{file_id[:8]}.pdf",
    )

# ── Utilities ────────────────────────────────────────────────────────────────
@app.delete("/api/cleanup/{file_id}")
async def cleanup(file_id: str):
    """Clean up storage for a specific file_id."""
    for d in [UPLOAD_DIR, PROCESSED_DIR]:
        p = d / f"{file_id}.pdf"
        if p.exists():
            p.unlink()
    return {"message": "Files delete ho gayi"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Server chal raha hai"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)