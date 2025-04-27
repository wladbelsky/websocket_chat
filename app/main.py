from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.containers import Container
from app.api import chat_routes, websocket_routes, user_routes
from app.core.db import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = app.container
    await container.broadcaster().connect()
    await create_tables() # Better use alembic for migrations, but this is a simple example
    
    yield
    
    await container.broadcaster().disconnect()


def create_app() -> FastAPI:
    container = Container()
    app = FastAPI(lifespan=lifespan)
    app.container = container

    # Include routers
    app.include_router(user_routes.router)
    app.include_router(chat_routes.router)
    app.include_router(websocket_routes.router)

    return app


app = create_app()
