import pathlib
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Depends
from fastapi.staticfiles import StaticFiles

import app.Controllers.admin as admin_controller
import app.Controllers.search as search_controller
from app.Services.authentication import permissive_access_token_verify, permissive_admin_token_verify
from app.Services.provider import ServiceProvider
from app.config import config
from .Models.api_response.base import WelcomeApiResponse, WelcomeApiAuthenticationResponse, \
    WelcomeApiAdminPortalAuthenticationResponse
from .util.fastapi_log_handler import init_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    provider = ServiceProvider()

    search_controller.services = provider
    admin_controller.services = provider
    yield


app = FastAPI(lifespan=lifespan)
init_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_controller.search_router, prefix="/search")
if config.admin_api_enable:
    app.include_router(admin_controller.admin_router, prefix="/admin")

if config.storage.method == "local":
    # Since we will check & create the static directory soon later when the StorageService initialized, we don't need to
    # check it here.
    app.mount("/static", StaticFiles(directory=pathlib.Path(config.storage.local.path), check_dir=False), name="static")


@app.get("/", description="Default portal. Test for server availability.")
def welcome(request: Request,
            token_passed: Annotated[bool, Depends(permissive_access_token_verify)],
            admin_token_passed: Annotated[bool, Depends(permissive_admin_token_verify)],
            ) -> WelcomeApiResponse:
    root_path: str = request.scope.get('root_path').rstrip('/')
    return WelcomeApiResponse(
        message="Ciallo~ Welcome to NekoImageGallery API!",
        server_time=datetime.now(),
        wiki={
            "openAPI": f"{root_path}/openapi.json",
            "swagger UI": f"{root_path}/docs",
            "redoc": f"{root_path}/redoc"
        },
        admin_api=WelcomeApiAdminPortalAuthenticationResponse(available=config.admin_api_enable,
                                                              passed=admin_token_passed),
        authorization=WelcomeApiAuthenticationResponse(required=config.access_protected, passed=token_passed),
        available_basis=["vision", "ocr"] if config.ocr_search.enable else ["vision"]
    )
