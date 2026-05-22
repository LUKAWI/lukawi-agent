"""FastAPI application factory for Lukawi server."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lukawi.server.routes import create_router
from lukawi.server.sse import create_sse_router


def create_app(state) -> FastAPI:
    app = FastAPI(title="Lukawi Agent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_router(state))
    app.include_router(create_sse_router(state))

    # Serve React static files if built
    web_dist = Path(__file__).resolve().parent / "static"
    if web_dist.exists():
        app.mount(
            "/", StaticFiles(directory=str(web_dist), html=True), name="static"
        )

    return app
