from io import BytesIO
from typing import Annotated
from uuid import uuid4, UUID

from PIL import Image
from fastapi import APIRouter, HTTPException
from fastapi.params import File, Query, Path, Depends
from loguru import logger

from app.Models.api_models.search_api_model import AdvancedSearchModel, CombinedSearchModel, SearchBasisEnum, \
    HybridSearchModel
from app.Models.api_response.search_api_response import SearchApiResponse
from app.Models.db_queries import DbQuery, DbQueryBasis, DbQueryCriteriaVector, DbQueryCriteriaId
from app.Models.query_params import SearchPagingParams, FilterParams
from app.Services.authentication import force_access_token_verify
from app.Services.provider import ServiceProvider
from app.config import config

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


async def query_and_postprocess(query: DbQuery, paging: SearchPagingParams,
                                filter_param: FilterParams) -> SearchApiResponse:
    results = await services.db_context.query_search(
        query=query,
        top_k=paging.count,
        skip=paging.skip,
        filter_param=filter_param,
    )
    return await result_postprocessing(
        SearchApiResponse(result=results, message=f"Successfully get {len(results)} results.", query_id=uuid4()))

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
    return await query_and_postprocess(
        query=DbQuery(criteria={
            basis.basis: DbQueryBasis(positive=[DbQueryCriteriaVector(vector=text_vector)])
        }),
        paging=paging,
        filter_param=filter_param,
    )


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
    return await query_and_postprocess(
        query=DbQuery(criteria={
            SearchBasisEnum.vision: DbQueryBasis(positive=[DbQueryCriteriaVector(vector=image_vector)])
        }),
        paging=paging,
        filter_param=filter_param,
    )


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
    return await query_and_postprocess(
        query=DbQuery(criteria={
            basis.basis: DbQueryBasis(positive=[DbQueryCriteriaId(id=str(image_id))]),
        }),
        paging=paging,
        filter_param=filter_param,
    )


@search_router.post("/advanced", description="Search with multiple criteria")
async def advancedSearch(
        model: AdvancedSearchModel,
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    logger.info("Advanced search request received: {}", model)
    criteria = process_advanced_search_vectors(model, basis)
    return await query_and_postprocess(
        query=DbQuery(criteria={
            basis.basis: criteria
        }),
        paging=paging,
        filter_param=filter_param,
    )


@search_router.post("/combined", description="Search with combined criteria. Deprecated, please use /hybrid instead.",
                    deprecated=True)
async def combinedSearch(
        model: CombinedSearchModel,
        basis: Annotated[SearchBasisParams, Depends(SearchBasisParams)],
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]) -> SearchApiResponse:
    if not config.ocr_search.enable:
        raise HTTPException(400, "You used combined search, but it needs OCR search which is not "
                                 "enabled.")
    logger.info("Combined search request received: {}", model)
    criteria = process_advanced_search_vectors(model, basis)
    match basis.basis:
        case SearchBasisEnum.ocr:
            second_basis = SearchBasisEnum.vision
            second_vector = services.transformers_service.get_text_vector(model.extra_prompt)
        case SearchBasisEnum.vision:
            second_basis = SearchBasisEnum.ocr
            second_vector = services.transformers_service.get_bert_vector(model.extra_prompt)
        case _:
            raise HTTPException(400, "Combined search only supports OCR and Vision basis.")

    return await query_and_postprocess(
        query=DbQuery(criteria={
            basis.basis: criteria,
            second_basis: DbQueryBasis(positive=[DbQueryCriteriaVector(vector=second_vector)])
        }),
        paging=paging,
        filter_param=filter_param,
    )


@search_router.post("/hybrid",
                    description="Search with hybrid criteria (vision and ocr). Will use RRF algorithm to combine the "
                                "hybrid results from both search results.")
async def hybrid_search(
        model: HybridSearchModel,
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)]
):
    logger.info("Hybrid search request received: {}", model)
    if not config.ocr_search.enable:
        raise HTTPException(400, "You used hybrid search, but it needs OCR search which is not "
                                 "enabled.")

    return await query_and_postprocess(
        query=DbQuery(criteria={
            SearchBasisEnum.vision: process_advanced_search_vectors(model.vision,
                                                                    SearchBasisParams(SearchBasisEnum.vision)),
            SearchBasisEnum.ocr: process_advanced_search_vectors(model.ocr, SearchBasisParams(SearchBasisEnum.ocr))
        }),
        paging=paging,
        filter_param=filter_param,
    )

@search_router.get("/random", description="Get random images")
async def randomPick(
        filter_param: Annotated[FilterParams, Depends(FilterParams)],
        paging: Annotated[SearchPagingParams, Depends(SearchPagingParams)],
        seed: Annotated[int | None, Query(
            description="The seed for random pick. This is helpful for generating a reproducible random pick.")] = None,
) -> SearchApiResponse:
    logger.info("Random pick request received")
    random_vector = services.transformers_service.get_random_vector(seed)
    return await query_and_postprocess(
        query=DbQuery(criteria={
            SearchBasisEnum.vision: DbQueryBasis(positive=[DbQueryCriteriaVector(vector=random_vector)])
        }),
        paging=paging,
        filter_param=filter_param,
    )


# @search_router.get("/recall/{query_id}", description="Recall the query with given queryId")
# async def recallQuery(query_id: str):
#     raise NotImplementedError()

def process_advanced_search_vectors(model: AdvancedSearchModel, basis: SearchBasisParams) -> DbQueryBasis:
    match basis.basis:
        case SearchBasisEnum.ocr:
            positive_vectors = [DbQueryCriteriaVector(vector=services.transformers_service.get_bert_vector(t)) for t in
                                model.criteria]
            negative_vectors = [DbQueryCriteriaVector(vector=services.transformers_service.get_bert_vector(t)) for t in
                                model.negative_criteria]
        case SearchBasisEnum.vision:
            positive_vectors = [DbQueryCriteriaVector(vector=services.transformers_service.get_text_vector(t)) for t in
                                model.criteria]
            negative_vectors = [DbQueryCriteriaVector(vector=services.transformers_service.get_text_vector(t)) for t in
                                model.negative_criteria]
        case _:  # pragma: no cover
            raise NotImplementedError()
    return DbQueryBasis(
        positive=positive_vectors,
        negative=negative_vectors,
        mix_strategy=model.mode
    )
