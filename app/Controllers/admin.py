from fastapi import APIRouter, Depends

from app.Services.authentication import force_admin_token_verify

admin_router = APIRouter(dependencies=[Depends(force_admin_token_verify)])


def add_image_info():
    pass
