# 📑 PDF Tool Suite — Complete Offline System

Ek powerful PDF tool jo **bina internet** ke aapke PC pe chalega.

---

## 🚀 Features

| Feature | Kya karta hai |
|---|---|
| ✏️ **PDF Edit** | Kisi bhi page pe text overlay add karein |
| 🗜️ **Compress** | File size kam karein (Ghostscript/PyMuPDF) |
| 🧹 **Pen Marks Remove** | Handwriting/pen strokes hatayein (OpenCV) |
| 🌙 **Color Invert** | Dark mode / light mode switch |
| 🔒 **Lock PDF** | Password protection add karein |
| 🔓 **Unlock PDF** | Password remove karein |

---

## 💻 System Requirements

- **Python 3.10+** (zaruri)
- **4 GB RAM** (minimum)
- **Windows 10/11** ya **Linux** ya **Mac**
- Internet: **Bilkul nahi chahiye** (sirf pehli baar setup ke liye)

---

## 📦 Installation Steps

### Windows

```
1. Python install karein: https://python.org/downloads
   (Install ke time "Add to PATH" ZARUR tick karein)

2. Is folder ko unzip karein (agar zip hai)

3. setup.bat double-click karein
   (dependencies automatically install ho jayengi)

4. start.bat double-click karein
   (server start ho jayega)

5. frontend/index.html ko Chrome/Edge mein open karein
```

### Linux / Mac

```bash
# Terminal mein yeh commands chalayein:
cd pdf_tool_suite
chmod +x setup.sh start.sh
./setup.sh      # ek baar setup
./start.sh      # server start
```

---

## 🖥️ Usage

1. `start.bat` (Windows) ya `./start.sh` (Linux/Mac) chalayein
2. Browser mein `frontend/index.html` open karein
3. Left sidebar se tool choose karein
4. PDF upload karein
5. Settings set karein
6. Process karein aur download karein

---

## 📁 Project Structure

```
pdf_tool_suite/
├── backend/
│   ├── main.py              ← FastAPI server (port 8000)
│   ├── requirements.txt     ← Python dependencies
│   ├── routers/
│   │   ├── edit.py          ← Text overlay
│   │   ├── compress.py      ← PDF compression
│   │   ├── clean.py         ← Handwriting removal
│   │   ├── invert.py        ← Color inversion
│   │   ├── lock.py          ← Password protection
│   │   └── unlock.py        ← Password removal
│   ├── uploads/             ← Temporary uploaded files
│   └── processed/           ← Processed output files
├── frontend/
│   └── index.html           ← Complete UI (React)
├── setup.bat                ← Windows setup
├── start.bat                ← Windows start
├── setup.sh                 ← Linux/Mac setup
├── start.sh                 ← Linux/Mac start
└── README.md                ← Yeh file
```

---

## ⚡ Optional: Ghostscript Install (Better Compression)

Ghostscript install karne se compression bahut better hogi:

**Windows:**
1. Download: https://www.ghostscript.com/download/gsdnld.html
2. Install karein (default settings)
3. System PATH mein add ho jayega automatically

**Linux:**
```bash
sudo apt install ghostscript
```

**Mac:**
```bash
brew install ghostscript
```

---

## 🔧 API Endpoints (Developers ke liye)

```
POST /api/upload           → PDF upload (returns file_id)
POST /api/edit             → Text add karein
POST /api/compress         → PDF compress karein
POST /api/clean            → Pen marks remove karein
POST /api/invert           → Colors invert karein
POST /api/lock             → Password add karein
POST /api/unlock           → Password remove karein
GET  /api/download/{id}    → Processed PDF download
DELETE /api/cleanup/{id}   → Files delete karein
GET  /api/health           → Server status check
```

Interactive API docs: http://localhost:8000/docs

---

## 🛡️ Privacy & Security

- ✅ Koi bhi file internet pe nahi jati
- ✅ Sab processing aapke PC pe hoti hai
- ✅ `uploads/` aur `processed/` folders mein temporarily save hoti hain
- ✅ Manually delete karne ke liye API ke `/api/cleanup/{id}` call karein

---

## ❓ Problems?

**"Module not found" error:** `setup.bat` dobara chalayein

**Port 8000 already in use:** 
```bash
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Linux:
lsof -ti:8000 | xargs kill
```

**OpenCV error on Linux:**
```bash
sudo apt install libgl1-mesa-glx
```
