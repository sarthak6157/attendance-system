"""Smart Attendance System - FastAPI Backend"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# CORS — allow all origins (fine for a college project; tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,             prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,            prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,         prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router,       prefix="/api/attendance", tags=["Attendance"])
app.include_router(courses.router,          prefix="/api/courses",    tags=["Courses"])
app.include_router(settings_router.router,  prefix="/api/settings",   tags=["Settings"])

# Serve the frontend HTML
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def serve_frontend():
    index = os.path.join(frontend_path, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "Smart Attendance API running. Visit /docs for API reference."}

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Smart Attendance API is running"}
