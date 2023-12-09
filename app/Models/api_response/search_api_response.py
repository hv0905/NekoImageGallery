from .base import NekoProtocol
from ..search_result import SearchResult
from uuid import UUID


class SearchApiResponse(NekoProtocol):
    query_id: UUID
    result: list[SearchResult]
