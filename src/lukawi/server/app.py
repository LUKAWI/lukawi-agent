"""FastAPI application factory for Lukawi server."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lukawi.server.routes import create_router
from lukawi.server.sse import create_sse_router

logger = logging.getLogger(__name__)


def create_app(state) -> FastAPI:
    app = FastAPI(title="Lukawi Agent", version="0.1.3")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_router(state))
    app.include_router(create_sse_router(state))

    @app.on_event("startup")
    async def _connect_mcp():
        if state.mcp_manager and state.mcp_configs:
            await state.mcp_manager.connect_all(state.mcp_configs)
            if state.tool_registry:
                await state.mcp_manager.register_tools(state.tool_registry)
            logger.info("MCP servers connected: %s", state.mcp_manager.connected_servers)

    @app.on_event("shutdown")
    async def _disconnect_mcp():
        if state.mcp_manager and state.mcp_manager.connected_count > 0:
            await state.mcp_manager.disconnect_all()
            logger.info("MCP servers disconnected")

    web_dist = Path(__file__).resolve().parent / "static"
    if web_dist.exists():
        app.mount(
            "/", StaticFiles(directory=str(web_dist), html=True), name="static"
        )

    return app
