from datetime import datetime
from typing import Annotated

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Depends
from fastapi.staticfiles import StaticFiles

from app.Controllers.admin import admin_router
from app.Controllers.search import searchRouter
from app.Services.authentication import permissive_access_token_verify
from app.config import config
from .Models.api_response.base import WelcomeApiResponse, WelcomeApiAuthenticationResponse
from .util.fastapi_log_handler import init_logging

app = FastAPI()
init_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(searchRouter, prefix="/search")
if config.admin_api_enable:
    app.include_router(admin_router, prefix="/admin")

if config.static_file.enable:
    app.mount("/static", StaticFiles(directory=config.static_file.path), name="static")


@app.get("/", description="Default portal. Test for server availability.")
def welcome(token_passed: Annotated[bool, Depends(permissive_access_token_verify)]) -> WelcomeApiResponse:
    return WelcomeApiResponse(
        message="Ciallo~ Welcome to NekoImageGallery API!",
        server_time=datetime.now(),
        wiki={
            "openAPI": "/openapi.json",
            "swagger UI": "/docs",
            "redoc": "/redoc"
        },
        authorization=WelcomeApiAuthenticationResponse(required=config.access_protected, passed=token_passed)
    )
