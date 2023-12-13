from datetime import datetime

from pydantic import BaseModel


class NekoProtocol(BaseModel):
    message: str


class WelcomeApiAuthenticationResponse(BaseModel):
    required: bool
    passed: bool


class WelcomeApiResponse(NekoProtocol):
    server_time: datetime
    wiki: dict[str, str]
    authorization: WelcomeApiAuthenticationResponse
    available_basis: list[str]
