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
    "https://attendance-system-tbon.onrender.com",  # your frontend on Render
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8080",
    "null",  # file:// opened locally in browser
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.onrender\.com",  # allow any Render subdomain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin",
                   "X-Requested-With", "Access-Control-Request-Method",
                   "Access-Control-Request-Headers"],
    expose_headers=["Content-Length"],
    max_age=600,
)

app.include_router(auth.router,             prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,            prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,         prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router,       prefix="/api/attendance", tags=["Attendance"])
app.include_router(courses.router,          prefix="/api/courses",    tags=["Courses"])
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
