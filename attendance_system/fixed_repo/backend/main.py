"""Smart Attendance System - FastAPI Backend"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from db.database import Base, engine
from routers import auth, users, sessions, attendance, courses, settings as settings_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Attendance System API", version="2.0.0")

@app.on_event("startup")
async def startup_event():
    print("Starting up — seeding database...")
    try:
        import seed
        seed.main()
        print("Seed complete.")
    except Exception as e:
        print(f"Seed failed (non-fatal): {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,            prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,           prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,        prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router,      prefix="/api/attendance", tags=["Attendance"])
app.include_router(courses.router,         prefix="/api/courses",    tags=["Courses"])
app.include_router(settings_router.router, prefix="/api/settings",   tags=["Settings"])

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Smart Attendance API is running"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_FRONTEND_PATHS = [
    os.path.join(BASE_DIR, "..", "frontend"),
    os.path.join(BASE_DIR, "frontend"),
    os.path.join(BASE_DIR, "..", "..", "frontend"),
]

FRONTEND_DIR = None
for path in POSSIBLE_FRONTEND_PATHS:
    resolved = os.path.realpath(path)
    if os.path.isdir(resolved):
        FRONTEND_DIR = resolved
        print(f"Frontend found at: {resolved}")
        break

if FRONTEND_DIR:
    try:
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="static")
    except Exception as e:
        print(f"Static mount warning: {e}")

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    if FRONTEND_DIR:
        index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index):
            with open(index, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse(content="""
    <html><body style="font-family:sans-serif;padding:40px;text-align:center;background:#f0f4fa;">
    <h2 style="color:#1a3c6e;">Smart Attendance API is Running</h2>
    <p>Frontend not found. Check that frontend/index.html exists in your repo.</p>
    <p><a href="/docs" style="color:#f08e1b;">View API Docs</a></p>
    </body></html>
    """)
