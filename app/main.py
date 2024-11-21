# import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from app.interfaces.api import api_router
from app.config import settings, database
from app.interfaces.error_handler import (
    ApplicationLevelException,
)


IS_PRODUCTION = settings.ENVIRONMENT == "production"

docs_paths = (
    {"openapi_url": "/", "docs_url": "/docs", "redoc_url": "/redoc"}
    if IS_PRODUCTION is False
    else {"openapi_url": None, "docs_url": None, "redoc_url": None}
)


# app startup handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    database.connect()
    yield
    # Shutdown logic
    database.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=docs_paths["openapi_url"],
    docs_url=docs_paths["docs_url"],
    redoc_url=docs_paths["redoc_url"],
    lifespan=lifespan,
)


# override default exception handler
# https://fastapi.tiangolo.com/tutorial/handling-errors/#override-the-default-exception-handlers
@app.exception_handler(ApplicationLevelException)
async def application_level_exception_handler(request: Request, exc: ApplicationLevelException):
    return JSONResponse(
        status_code=200,
        content={
            "message": exc.msg,
            "success": False,
        },
    )


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# set app router
app.include_router(api_router, prefix=settings.API_V1_STR)
