from urllib.parse import urlparse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.Services.provider import storage_service
from app.Services.storage.local_storage import LocalStorage
from app.Models.api_response.search_api_response import SearchApiResponse


class PresignUrlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # It is assumed that the user's server will be using the same storage service as when the index was built,
        # as this is the only way to read the url correctly. Currently only s3 storage need to presign url
        response = await call_next(request)
        scope = getattr(request, "scope", {})
        route = scope.get("route", None)
        tags = getattr(route, "tags", [])
        if not isinstance(storage_service.active_storage, LocalStorage) and "Search" in tags:
            response_body = b""
            # noinspection PyUnresolvedReferences
            async for chunk in response.body_iterator:
                response_body += chunk
            response_cls = SearchApiResponse.model_validate_json(json_data=response_body)
            # Assume url is a standard s3 url
            for itm in response_cls.result:
                itm.img.url = await self._get_presign_url(itm.img.url)
                if itm.img.thumbnail_url:
                    itm.img.thumbnail_url = await self._get_presign_url(itm.img.thumbnail_url)
            new_content = response_cls.model_dump_json()
            new_headers = self._modify_content_length(dict(response.headers), new_content)
            return Response(content=new_content, status_code=response.status_code,
                            headers=new_headers, media_type=response.media_type)
        return response

    @staticmethod
    async def _get_presign_url(ori_url: str) -> str:
        url_path = urlparse(ori_url).path
        filename = storage_service.active_storage.static_dir.name
        fixed_path = url_path.split(f"/{filename}")[-1]
        sign_url = await storage_service.active_storage.presign_url(fixed_path)
        return sign_url

    @staticmethod
    def _modify_content_length(ori_headers: dict, ori_content: str):
        ori_headers["content-length"] = str(len(ori_content.encode()))
        return ori_headers
