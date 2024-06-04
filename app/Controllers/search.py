from io import BytesIO
from typing import Annotated, List, Union
from uuid import uuid4, UUID

from PIL import Image
from fastapi import APIRouter, HTTPException
from fastapi.params import File, Query, Path, Depends
from loguru import logger

from app.Models.api_models.search_api_model import AdvancedSearchModel, CombinedSearchModel, SearchBasisEnum, \
    SearchCombinedBasisEnum
from app.Models.api_response.search_api_response import SearchApiResponse
from app.Models.query_params import SearchPagingParams, FilterParams
from app.Models.search_result import SearchResult
from app.Services.authentication import force_access_token_verify
from app.Services.provider import ServiceProvider
from app.config import config
from app.util.calculate_vectors_cosine import calculate_vectors_cosine

search_router = APIRouter(dependencies=([Depends(force_access_token_verify)] if config.access_protected else None),
                          tags=["Search"])

services: ServiceProvider | None = None  # The service provider will be injected in the webapp initialize


class SearchBasisParams:
    def __init__(self,
                 basis: Annotated[SearchBasisEnum, Query(
                     description="The basis used to search the image.")] = SearchBasisEnum.vision):
        if basis == SearchBasisEnum.ocr and not config.ocr_search.enable:
            raise HTTPException(400, "OCR search is not enabled.")
        self.basis = basis


class SearchCombinedParams:
    def __init__(self,
                 basis: Annotated[SearchCombinedBasisEnum, Query(
                     description="The primary basis used for searching the image.")] = SearchCombinedBasisEnum.vision):
        if not config.ocr_search.enable:
            raise HTTPException(400, "You used combined search, but it needs OCR search which is not "
                                     "enabled.")
        self.basis = basis


async def result_postprocessing(resp: SearchApiResponse) -> SearchApiResponse:
    if not config.storage.method.enabled:
        return resp
    for item in resp.result:
        if item.img.local:
            img_extension = item.img.format or item.img.url.split('.')[-1]
            img_remote_filename = f"{item.img.id}.{img_extension}"
            item.img.url = await services.storage_service.active_storage.presign_url(img_remote_filename)
        if item.img.thumbnail_url is not None and (item.img.local or item.img.local_thumbnail):
            thumbnail_remote_filename = f"thumbnails/{item.img.id}.webp"
            item.img.thumbnail_url = await services.storage_service.active_storage.presign_url(
                thumbnail_remote_filename)
    return resp


@search_router.get("/text/{prompt}", description="Search images by text prompt")
async def textSearch(
        prompt: Annotated[
            str, Path(max_length=100, description="The image prompt text you want to search.")],
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)],
        exact: Annotated[bool, Query(
            description="If using OCR search, this option will require the ocr text contains **exactly** the "
                        "criteria you have given. This won't take any effect in vision search.")] = False
) -> SearchApiResponse:
    logger.info("Text search request received, prompt: {}", prompt)
    text_vector = services.transformers_service.get_text_vector(prompt) if basis.basis == SearchBasisEnum.vision \
        else services.transformers_service.get_bert_vector(prompt)
    if basis.basis == SearchBasisEnum.ocr and exact:
        filter_param.ocr_text = prompt
    results = await services.db_context.querySearch(text_vector,
                                                    query_vector_name=services.db_context.getVectorByBasis(basis.basis),
                                                    filter_param=filter_param,
                                                    top_k=paging.count,
                                                    skip=paging.skip)
    return await result_postprocessing(
        SearchApiResponse(result=results, message=f"Successfully get {len(results)} results.", query_id=uuid4()))


@search_router.post("/image", description="Search images by image")
async def imageSearch(
        image: Annotated[bytes, File(max_length=10 * 1024 * 1024, media_type="image/*",
                                     description="The image you want to search.")],
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]
) -> SearchApiResponse:
    fakefile = BytesIO(image)
    img = Image.open(fakefile)
    logger.info("Image search request received")
    image_vector = services.transformers_service.get_image_vector(img)
    results = await services.db_context.querySearch(image_vector,
                                                    top_k=paging.count,
                                                    skip=paging.skip,
                                                    filter_param=filter_param)
    return await result_postprocessing(
        SearchApiResponse(result=results, message=f"Successfully get {len(results)} results.", query_id=uuid4()))


@search_router.get("/similar/{image_id}",
                   description="Search images similar to the image with given id. "
                               "Won't include the given image itself in the result.")
async def similarWith(
        image_id: Annotated[UUID, Path(description="The id of the image you want to search.")],
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]
) -> SearchApiResponse:
    logger.info("Similar search request received, id: {}", image_id)
    results = await services.db_context.querySimilar(search_id=str(image_id),
                                                     top_k=paging.count,
                                                     skip=paging.skip,
                                                     filter_param=filter_param,
                                                     query_vector_name=services.db_context.getVectorByBasis(
                                                         basis.basis))
    return await result_postprocessing(
        SearchApiResponse(result=results, message=f"Successfully get {len(results)} results.", query_id=uuid4()))


@search_router.post("/advanced", description="Search with multiple criteria")
async def advancedSearch(
        model: AdvancedSearchModel,
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    if len(model.criteria) + len(model.negative_criteria) == 0:
        raise HTTPException(status_code=422, detail="At least one criteria should be provided.")
    logger.info("Advanced search request received: {}", model)
    result = await process_advanced_and_combined_search_query(model, basis, filter_param, paging)
    return await result_postprocessing(
        SearchApiResponse(result=result, message=f"Successfully get {len(result)} results.", query_id=uuid4()))


@search_router.post("/combined", description="Search with combined criteria")
async def combinedSearch(
        model: CombinedSearchModel,
        basis: Annotated[SearchCombinedParams, Depends(SearchCombinedParams)],
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    if len(model.criteria) + len(model.negative_criteria) == 0:
        raise HTTPException(status_code=422, detail="At least one criteria should be provided.")
    logger.info("Combined search request received: {}", model)
    result = await process_advanced_and_combined_search_query(model, basis, filter_param, paging)
    calculate_and_sort_by_combined_scores(model, basis, result)
    result = result[:paging.count] if len(result) > paging.count else result
    return await result_postprocessing(
        SearchApiResponse(result=result, message=f"Successfully get {len(result)} results.", query_id=uuid4()))


@search_router.get("/random", description="Get random images")
async def randomPick(
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    logger.info("Random pick request received")
    random_vector = services.transformers_service.get_random_vector()
    result = await services.db_context.querySearch(random_vector, top_k=paging.count, filter_param=filter_param)
    return await result_postprocessing(
        SearchApiResponse(result=result, message=f"Successfully get {len(result)} results.", query_id=uuid4()))


@search_router.get("/recall/{query_id}", description="Recall the query with given queryId")
async def recallQuery(query_id: str):
    raise NotImplementedError()


async def process_advanced_and_combined_search_query(model: Union[AdvancedSearchModel, CombinedSearchModel],
                                                     basis: Union[SearchBasisParams, SearchCombinedParams],
                                                     filter_param: FilterParams,
                                                     paging: SearchPagingParams) -> List[SearchResult]:
    if basis.basis == SearchBasisEnum.ocr:
        positive_vectors = [services.transformers_service.get_bert_vector(t) for t in model.criteria]
        negative_vectors = [services.transformers_service.get_bert_vector(t) for t in model.negative_criteria]
    else:
        positive_vectors = [services.transformers_service.get_text_vector(t) for t in model.criteria]
        negative_vectors = [services.transformers_service.get_text_vector(t) for t in model.negative_criteria]
    # In order to ensure the query effect of the combined query, modify the actual top_k
    _query_top_k = min(max(30, paging.count * 3), 100) if isinstance(model, CombinedSearchModel) else paging.count
    result = await services.db_context.querySimilar(query_vector_name=services.db_context.getVectorByBasis(basis.basis),
                                                    positive_vectors=positive_vectors,
                                                    negative_vectors=negative_vectors,
                                                    mode=model.mode,
                                                    filter_param=filter_param,
                                                    with_vectors=True if isinstance(basis,
                                                                                    SearchCombinedParams) else False,
                                                    top_k=_query_top_k,
                                                    skip=paging.skip)
    return result


def calculate_and_sort_by_combined_scores(model: CombinedSearchModel,
                                          basis: SearchCombinedParams,
                                          result: List[SearchResult]) -> None:
    # First, calculate the extra prompt vector
    extra_prompt_vector = services.transformers_service.get_text_vector(model.extra_prompt) \
        if basis.basis == SearchCombinedBasisEnum.ocr \
        else services.transformers_service.get_bert_vector(model.extra_prompt)
    # Then, calculate combined_similar_score (original score * similar_score) and write to SearchResult.score
    for itm in result:
        extra_vector = itm.img.image_vector if itm.img.image_vector is not None else itm.img.text_contain_vector
        similar_score = calculate_vectors_cosine(extra_vector, extra_prompt_vector)
        itm.score = similar_score * itm.score
    # Finally, sort the result by combined_similar_score
    result.sort(key=lambda i: i.score, reverse=True)
