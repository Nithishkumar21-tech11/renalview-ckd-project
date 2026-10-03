from __future__ import annotations
import io
import re
from pathlib import Path
from typing import Literal
import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "ckd_demo_model.joblib"
FEATURES = ["bp", "sg", "al", "su", "rbc", "bu", "sc", "sod", "pot", "hemo", "wbcc", "rbcc", "htn"]
ALIASES = {
    "bp": [r"blood pressure", r"\bbp\b"],
    "sg": [r"specific gravity", r"\bsg\b"],
    "al": [r"urine albumin", r"albumin", r"\bal\b"],
    "su": [r"urine sugar", r"\bsugar\b", r"\bsu\b"],
    "bu": [r"blood urea", r"\bbun\b", r"\bbu\b"],
    "sc": [r"serum creatinine", r"\bcreatinine\b", r"\bsc\b"],
    "sod": [r"\bsodium\b", r"\bsod\b"],
    "pot": [r"\bpotassium\b", r"\bpot\b"],
    "hemo": [r"\bhemoglobin\b", r"\bhaemoglobin\b", r"\bhemo\b"],
    "wbcc": [r"white blood cell count", r"\bwbcc\b"],
    "rbcc": [r"red blood cell count", r"\brbcc\b"],
    "rbc": [r"red blood cells? in urine", r"urine red blood cells?", r"\brbc\b"],
    "htn": [r"\bhypertension\b", r"\bhtn\b"],
}

app = FastAPI(title="RenalView CKD Record Review", docs_url=None, redoc_url=None)
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")
if not MODEL_PATH.exists():
    raise RuntimeError("Missing ckd_demo_model.joblib beside server.py")
model = joblib.load(MODEL_PATH)

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok"}

def extract_values(text: str) -> dict:
    lines = text.splitlines()
    found = {}
    for key in FEATURES:
        for line in lines:
            if key == "rbc" and re.search(r"red blood cell count|\brbcc\b", line, re.I):
                continue
            for alias in ALIASES[key]:
                match = re.search(alias, line, re.I)
                if not match:
                    continue
                tail = line[match.end():]
                if key in ("rbc", "htn"):
                    value_match = re.search(r"\b(normal|abnormal|yes|no|positive|negative)\b", tail, re.I)
                    if value_match:
                        found[key] = 1 if value_match.group(1).lower() in ("normal", "yes", "positive") else 0
                else:
                    value_match = re.search(r"[-+]?\d+(?:\.\d+)?", tail.replace(",", ""))
                    if value_match:
                        found[key] = float(value_match.group())
                if key in found:
                    break
            if key in found:
                break
    return found

@app.post("/api/extract")
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Choose a PDF file.")
    content = await file.read(12 * 1024 * 1024 + 1)
    if len(content) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF must be 12 MB or smaller.")
    try:
        reader = PdfReader(io.BytesIO(content))
        if len(reader.pages) > 30:
            raise HTTPException(status_code=413, detail="PDF must have 30 pages or fewer.")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read this PDF.") from exc
    if not text.strip():
        raise HTTPException(status_code=422, detail="No selectable text found. Scanned PDFs are not supported yet.")
    values = extract_values(text)
    return {"values": values, "found": len(values), "total": len(FEATURES)}

class PatientValues(BaseModel):
    bp: float = Field(ge=0, le=200)
    sg: float = Field(ge=1, le=1.05)
    al: float = Field(ge=0, le=5)
    su: float = Field(ge=0, le=5)
    rbc: Literal[0, 1]
    bu: float = Field(ge=0, le=200)
    sc: float = Field(ge=0, le=20)
    sod: float = Field(ge=100, le=160)
    pot: float = Field(ge=2, le=10)
    hemo: float = Field(ge=0, le=25)
    wbcc: float = Field(ge=1000, le=50000)
    rbcc: float = Field(ge=0, le=10)
    htn: Literal[0, 1]

@app.post("/api/predict")
def predict(values: PatientValues):
    row = values.model_dump()
    sample = pd.DataFrame([[row[name] for name in FEATURES]], columns=FEATURES)
    prediction = int(model.predict(sample)[0])
    return {"label": "CKD" if prediction == 1 else "Not CKD"}
