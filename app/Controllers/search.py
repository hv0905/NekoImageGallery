from io import BytesIO
from typing import Annotated
from uuid import uuid4, UUID

from PIL import Image
from fastapi import APIRouter, HTTPException
from fastapi.params import File, Query, Path, Depends
from loguru import logger

from app.Models.api_model import AdvancedSearchModel, SearchBasisEnum
from app.Models.api_response.search_api_response import SearchApiResponse
from app.Services import db_context
from app.Services import transformers_service
from app.Services.authentication import force_access_token_verify
from app.config import config

searchRouter = APIRouter(dependencies=([Depends(force_access_token_verify)] if config.access_protected else None))


class SearchPagingParams:
    def __init__(
            self,
            count: Annotated[int, Query(ge=1, le=100, description="The number of results you want to get.")] = 10
    ):
        self.count = count


class SearchBasisParams:
    def __init__(self,
                 basis: Annotated[SearchBasisEnum, Query(
                     description="The basis used to search the image.")] = SearchBasisEnum.vision):
        if basis == SearchBasisEnum.ocr and not config.ocr_search.enable:
            raise HTTPException(400, "OCR search is not enabled.")
        self.basis = basis


@searchRouter.get("/text/{prompt}", description="Search images by text prompt")
async def textSearch(
        prompt: Annotated[
            str, Path(min_length=3, max_length=100, description="The image prompt text you want to search.")],
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]
) -> SearchApiResponse:
    logger.info("Text search request received, prompt: {}", prompt)
    text_vector = transformers_service.get_text_vector(prompt) if basis.basis == SearchBasisEnum.vision \
        else transformers_service.get_bert_vector(prompt)
    results = await db_context.querySearch(text_vector,
                                           query_vector_name=db_context.getVectorByBasis(basis.basis),
                                           top_k=paging.count)
    return SearchApiResponse(result=results, message=f"Successfully get {len(results)} results.", query_id=uuid4())


@searchRouter.post("/image", description="Search images by image")
async def imageSearch(
        image: Annotated[bytes, File(max_length=10 * 1024 * 1024, media_type="image/*",
                                     description="The image you want to search.")],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    fakefile = BytesIO(image)
    img = Image.open(fakefile)
    logger.info("Image search request received")
    image_vector = transformers_service.get_image_vector(img)
    results = await db_context.querySearch(image_vector, top_k=paging.count)
    return SearchApiResponse(result=results, message=f"Successfully get {len(results)} results.", query_id=uuid4())


@searchRouter.get("/similar/{id}",
                  description="Search images similar to the image with given id. "
                              "Won't include the given image itself in the result.")
async def similarWith(
        id: Annotated[UUID, Path(description="The id of the image you want to search.")],
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]
) -> SearchApiResponse:
    logger.info("Similar search request received, id: {}", id)
    results = await db_context.querySimilar(str(id),
                                            top_k=paging.count,
                                            query_vector_name=db_context.getVectorByBasis(basis.basis))
    return SearchApiResponse(result=results, message=f"Successfully get {len(results)} results.", query_id=uuid4())


@searchRouter.post("/advanced", description="Search with multiple criteria")
async def advancedSearch(
        model: AdvancedSearchModel,
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    if len(model.criteria) + len(model.negative_criteria) == 0:
        raise ValueError("At least one criteria should be provided.")
    logger.info("Advanced search request received: {}", model)
    positive_vectors = [transformers_service.get_text_vector(t) for t in model.criteria]
    negative_vectors = [transformers_service.get_text_vector(t) for t in model.negative_criteria]
    result = await db_context.queryAdvanced(positive_vectors, negative_vectors,
                                            db_context.getVectorByBasis(basis.basis), model.mode,
                                            top_k=paging.count)
    return SearchApiResponse(result=result, message=f"Successfully get {len(result)} results.", query_id=uuid4())


@searchRouter.get("/random", description="Get random images")
async def randomPick(paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    logger.info("Random pick request received")
    random_vector = transformers_service.get_random_vector()
    result = await db_context.querySearch(random_vector, top_k=paging.count)
    return SearchApiResponse(result=result, message=f"Successfully get {len(result)} results.", query_id=uuid4())


@searchRouter.get("/recall/{queryId}", description="Recall the query with given queryId")
async def recallQuery(queryId: str):
    raise NotImplementedError()
