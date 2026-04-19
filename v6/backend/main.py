"""Smart Attendance System — FastAPI Backend v3"""
import sys, os, time
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from db.database import Base, engine
from routers import auth, users, sessions, attendance, courses, settings as settings_router, timetable

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Smart Attendance System API", version="3.1.0")

@app.on_event("startup")
async def startup_event():
    print("Starting up — seeding database...")
    try:
        import seed; seed.main()
        print("Seed complete.")
    except Exception as e:
        print(f"Seed failed (non-fatal): {e}")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://attendance-system-tbon.onrender.com",
        "https://attendance-system-tbon.onrender.com/",
        "https://smart-attendance-portal.onrender.com",
        "https://smart-attendance-portal.onrender.com/",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiter — login brute-force protection ───────────────────────────────
_login_attempts: dict = defaultdict(list)
RATE_LIMIT_MAX    = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/api/auth/login" and request.method == "POST":
        ip = request.client.host or "unknown"
        now = time.time()
        _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
        if len(_login_attempts[ip]) >= RATE_LIMIT_MAX:
            wait = int(RATE_LIMIT_WINDOW - (now - _login_attempts[ip][0]))
            raise HTTPException(status_code=429, detail=f"Too many login attempts. Try again in {wait} seconds.")
        _login_attempts[ip].append(now)
    return await call_next(request)

# ── CSP middleware ────────────────────────────────────────────────────────────
from starlette.middleware.base import BaseHTTPMiddleware

class PermissiveCSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "script-src * 'unsafe-inline' 'unsafe-eval' blob:; "
            "connect-src * data: blob:; img-src * data: blob:; "
            "font-src * data:; style-src * 'unsafe-inline';"
        )
        return response

app.add_middleware(PermissiveCSPMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,            prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,           prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,        prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router,      prefix="/api/attendance", tags=["Attendance"])
app.include_router(courses.router,         prefix="/api/courses",    tags=["Courses"])
app.include_router(settings_router.router, prefix="/api/settings",   tags=["Settings"])
app.include_router(timetable.router,       prefix="/api/timetable",  tags=["Timetable"])

# ── Audit log (in-memory) ─────────────────────────────────────────────────────
_audit_log: list = []

@app.post("/api/audit/log")
async def add_audit(request: Request):
    body = await request.json()
    _audit_log.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": body.get("action",""), "by": body.get("by",""),
        "target": body.get("target",""), "detail": body.get("detail",""),
    })
    if len(_audit_log) > 500: _audit_log.pop(0)
    return {"ok": True}

@app.get("/api/audit/log")
async def get_audit():
    return list(reversed(_audit_log))

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.1.0"}

# ── Serve frontend ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = None
for path in [os.path.join(BASE_DIR, "..", "frontend"), os.path.join(BASE_DIR, "frontend")]:
    r = os.path.realpath(path)
    if os.path.isdir(r):
        FRONTEND_DIR = r; break

if FRONTEND_DIR:
    try: app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="static")
    except: pass

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    if FRONTEND_DIR:
        idx = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(idx):
            with open(idx, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>API running. Visit <a href='/docs'>/docs</a></h2>")
