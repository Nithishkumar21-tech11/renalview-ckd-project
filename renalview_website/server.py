from __future__ import annotations

import hashlib
import hmac
import io
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pypdf import PdfReader
from starlette.middleware.sessions import SessionMiddleware

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "ckd_demo_model.joblib"
DB_PATH = ROOT / "renalview_users.sqlite3"
SESSION_SECRET = os.getenv("RENALVIEW_SESSION_SECRET") or secrets.token_urlsafe(32)
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
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=os.getenv("RENALVIEW_HTTPS_ONLY", "0") == "1",
    max_age=60 * 60 * 12,
)
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")
if not MODEL_PATH.exists():
    raise RuntimeError("Missing ckd_demo_model.joblib beside server.py")
model = joblib.load(MODEL_PATH)


def connect_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL UNIQUE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


initialize_database()


def require_login(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Please sign in to continue.")


def normalize_identifier(raw: str) -> str:
    value = raw.strip()
    if "@" in value:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise HTTPException(status_code=422, detail="Enter a valid email address or mobile number.")
        return value.lower()
    phone = re.sub(r"[\s()\-]", "", value)
    if phone.startswith("00"):
        phone = "+" + phone[2:]
    if not re.fullmatch(r"\+?[1-9]\d{7,14}", phone):
        raise HTTPException(status_code=422, detail="Enter a valid email address or mobile number, including country code.")
    return phone


def password_digest(password: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 310_000)
    return digest.hex()


@app.get("/", include_in_schema=False)
def home(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/signin", status_code=303)
    return FileResponse(ROOT / "index.html")


@app.get("/signin", include_in_schema=False)
def signin_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/", status_code=303)
    return FileResponse(ROOT / "signin.html")


class AuthPayload(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=200)


@app.post("/api/auth/register")
def register(payload: AuthPayload, request: Request):
    identifier = normalize_identifier(payload.identifier)
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Choose a password with at least 8 characters.")
    salt = secrets.token_hex(16)
    digest = password_digest(payload.password, salt)
    try:
        with connect_db() as connection:
            cursor = connection.execute(
                "INSERT INTO users(identifier, salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (identifier, salt, digest, datetime.now(timezone.utc).isoformat()),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email or mobile number already exists.") from exc
    request.session["user"] = identifier
    request.session["user_id"] = user_id
    return {"ok": True, "identifier": identifier}


@app.post("/api/auth/login")
def login(payload: AuthPayload, request: Request):
    identifier = normalize_identifier(payload.identifier)
    with connect_db() as connection:
        user = connection.execute("SELECT id, identifier, salt, password_hash FROM users WHERE identifier = ?", (identifier,)).fetchone()
    if not user or not hmac.compare_digest(password_digest(payload.password, user["salt"]), user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email/mobile number or password is incorrect.")
    request.session.clear()
    request.session["user"] = user["identifier"]
    request.session["user_id"] = user["id"]
    return {"ok": True, "identifier": user["identifier"]}


@app.post("/api/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


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
async def extract_pdf(request: Request, file: UploadFile = File(...)):
    require_login(request)
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
def predict(request: Request, values: PatientValues):
    require_login(request)
    row = values.model_dump()
    sample = pd.DataFrame([[row[name] for name in FEATURES]], columns=FEATURES)
    prediction = int(model.predict(sample)[0])
    return {"label": "CKD" if prediction == 1 else "Not CKD"}
