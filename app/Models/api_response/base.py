from pydantic import BaseModel
from datetime import datetime


class NekoProtocol(BaseModel):
    message: str


class WelcomeApiResponse(NekoProtocol):
    server_time: datetime
    wiki: dict[str, str]
