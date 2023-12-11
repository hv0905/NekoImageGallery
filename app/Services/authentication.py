from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Header

from app.config import config


def verify_access_token(token: str | None) -> bool:
    if not config.access_protected:
        return True
    return token is not None and token == config.access_token


def force_access_token_verify(
        x_access_token: Annotated[str | None, Header(
            description="Access token set in configuration (if access_protected is enabled)")] = None):
    if not verify_access_token(x_access_token):
        raise HTTPException(status_code=401, detail="Access token is not present or invalid.")


def permissive_access_token_verify(
        x_access_token: Annotated[str | None, Header(
            description="Access token set in configuration (if access_protected is enabled)")] = None) -> bool:
    return verify_access_token(x_access_token)
