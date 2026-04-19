"""Smart Attendance System — FastAPI Backend v3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from db.database import Base, engine
from routers import auth, users, sessions, attendance, courses, settings as settings_router, timetable, branches

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

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
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
app.include_router(branches.router,         prefix="/api/branches",   tags=["Branches"])
app.include_router(settings_router.router,  prefix="/api/settings",   tags=["Settings"])
app.include_router(timetable.router,        prefix="/api/timetable",  tags=["Timetable"])

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}

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
