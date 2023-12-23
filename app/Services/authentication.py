from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Header, Depends

from app.config import config


def verify_access_token(token: str | None) -> bool:
    if not config.access_protected:
        return True
    return token is not None and token == config.access_token


def permissive_access_token_verify(
        x_access_token: Annotated[str | None, Header(
            description="Access token set in configuration (if access_protected is enabled)")] = None) -> bool:
    return verify_access_token(x_access_token)


def force_access_token_verify(token_passed: Annotated[bool, Depends(permissive_access_token_verify)]):
    if not token_passed:
        raise HTTPException(status_code=401, detail="Access token is not present or invalid.")


def permissive_admin_token_verify(
        x_admin_token: Annotated[str | None, Header(
            description="Admin token set in configuration (if admin_api_enable is enabled)")] = None) -> bool:
    return x_admin_token == config.admin_token


def force_admin_token_verify(token_passed: Annotated[bool, Depends(permissive_admin_token_verify)]):
    if not token_passed:
        raise HTTPException(status_code=401, detail="Admin token is not present or invalid.")
