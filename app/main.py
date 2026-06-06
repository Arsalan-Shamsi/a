"""FastAPI app: serves the dashboard data and the static page.

Run it with:   uvicorn app.main:app --reload
Then open:      http://localhost:8000
Interactive API docs are auto-generated at http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .aggregate import build_dashboard
from .config import LIVE, STATIC_DIR

app = FastAPI(
    title="Local Illness Dashboard",
    version="0.1.0",
    description="What's going around right now — flu, COVID, and RSV — from public health data.",
)


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "live" if LIVE else "sample"}


@app.get("/api/dashboard")
def dashboard():
    """The whole payload the page renders: current levels, trends, and sources."""
    return JSONResponse(build_dashboard().to_dict())


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


# Static assets (JS/CSS) live under /static.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
