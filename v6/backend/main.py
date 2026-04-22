"""Smart Attendance System — FastAPI Backend v3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from db.database import Base, engine
from routers import auth, users, sessions, attendance, courses, settings as settings_router, timetable

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Smart Attendance System API", version="3.0.0")

@app.on_event("startup")
async def startup_event():
    print("Starting up — seeding database...")
    try:
        import seed; seed.main()
        print("Seed complete.")
    except Exception as e:
        print(f"Seed failed (non-fatal): {e}")

ALLOWED_ORIGINS = [
    "https://attendance-system-tbon.onrender.com",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "*",  # Remove this in production for stricter security
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class PermissiveCSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Allow loading face-api models from external CDNs
        response.headers["Content-Security-Policy"] = (
            "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "script-src * 'unsafe-inline' 'unsafe-eval' blob:; "
            "connect-src * data: blob:; "
            "img-src * data: blob:; "
            "font-src * data:; "
            "style-src * 'unsafe-inline';"
        )
        return response

app.add_middleware(PermissiveCSPMiddleware)

app.include_router(auth.router,             prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,            prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,         prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router,       prefix="/api/attendance", tags=["Attendance"])
app.include_router(courses.router,          prefix="/api/courses",    tags=["Courses"])
app.include_router(settings_router.router,  prefix="/api/settings",   tags=["Settings"])
app.include_router(timetable.router,        prefix="/api/timetable",  tags=["Timetable"])

# ── In-memory audit log ──────────────────────────────────────────────────────
_audit_log = []

@app.post("/api/audit/log")
async def record_audit(entry: dict, request: Request):
    from datetime import datetime as dt
    _audit_log.insert(0, {**entry, "server_time": dt.utcnow().isoformat(), "ip": request.client.host})
    if len(_audit_log) > 500: _audit_log.pop()
    return {"ok": True}

@app.get("/api/audit/log")
async def get_audit():
    return _audit_log[:200]


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/manifest.json")
def serve_manifest():
    import json
    from fastapi.responses import JSONResponse
    manifest = {
        "name": "Smart Attendance — TMU",
        "short_name": "Attendance",
        "description": "Smart Attendance System for Teerthanker Mahaveer University",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1a3c6e",
        "theme_color": "#1a3c6e",
        "orientation": "portrait-primary",
        "icons": [{"src": "/favicon.ico", "sizes": "any", "type": "image/x-icon"}],
        "categories": ["education", "productivity"]
    }
    return JSONResponse(content=manifest, headers={"Content-Type": "application/manifest+json"})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = None
for path in [os.path.join(BASE_DIR, "..", "frontend"), os.path.join(BASE_DIR, "frontend")]:
    r = os.path.realpath(path)
    if os.path.isdir(r):
        FRONTEND_DIR = r; break

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    if FRONTEND_DIR:
        idx = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(idx):
            with open(idx, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>API running. Visit <a href='/docs'>/docs</a></h2>")

# Mount static files at root LAST so API routes take priority.
# html=True enables SPA fallback — unmatched paths serve index.html
# instead of returning 404, which is required for client-side routing.
if FRONTEND_DIR:
    try: app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")
    except: pass
