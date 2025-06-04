import numpy
from grpc.aio import AioRpcError
from httpx import HTTPError
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import FusionQuery, NearestQuery
from qdrant_client.models import RecommendStrategy, RecommendInput, RecommendQuery, Prefetch

from app.Models.api_models.search_api_model import SearchModelEnum, SearchBasisEnum
from app.Models.db_queries import DbQuery, DbQueryBasis, DbQueryCriteria, DbQueryCriteriaId, DbQueryCriteriaVector
from app.Models.mapped_image import MappedImage
from app.Models.query_params import FilterParams
from app.Models.search_result import SearchResult
from app.Services.lifespan_service import LifespanService
from app.config import config, QdrantMode
from app.util.retry_deco_async import wrap_object, retry_async


class PointNotFoundError(ValueError):
    def __init__(self, point_id: str):
        self.point_id = point_id
        super().__init__(f"Point {point_id} not found.")


class VectorDbContext(LifespanService):
    IMG_VECTOR = "image_vector"
    TEXT_VECTOR = "text_contain_vector"
    AVAILABLE_POINT_TYPES = models.Record | models.ScoredPoint | models.PointStruct

    def __init__(self):
        match config.qdrant.mode:
            case QdrantMode.SERVER:
                self._client = AsyncQdrantClient(host=config.qdrant.host, port=config.qdrant.port,
                                                 grpc_port=config.qdrant.grpc_port, api_key=config.qdrant.api_key,
                                                 prefer_grpc=config.qdrant.prefer_grpc)
                wrap_object(self._client, retry_async((AioRpcError, HTTPError)))
            case QdrantMode.LOCAL:
                self._client = AsyncQdrantClient(path=config.qdrant.local_path)
            case QdrantMode.MEMORY:
                logger.warning("Using in-memory Qdrant client. Data will be lost after application restart. "
                               "This should only be used for testing and debugging.")
                self._client = AsyncQdrantClient(":memory:")
            case _:
                raise ValueError("Invalid Qdrant mode.")
        self.collection_name = config.qdrant.coll

    async def on_load(self):
        if not await self.check_collection():
            logger.warning("Collection not found. Initializing...")
            await self.initialize_collection()

    async def retrieve_by_id(self, image_id: str, with_vectors=False) -> MappedImage:
        """
        Retrieve an item from database by id. Will raise PointNotFoundError if the given ID doesn't exist.
        :param image_id: The ID to retrieve.
        :param with_vectors: Whether to retrieve vectors.
        :return: The retrieved item.
        """
        logger.info("Retrieving item {} from database...", image_id)
        result = await self._client.retrieve(collection_name=self.collection_name,
                                             ids=[image_id],
                                             with_payload=True,
                                             with_vectors=with_vectors)
        if len(result) != 1:
            logger.error("Point not exist.")
            raise PointNotFoundError(image_id)
        return self._get_mapped_image_from_point(result[0])

    async def retrieve_by_ids(self, image_id: list[str], with_vectors=False) -> list[MappedImage]:
        """
        Retrieve items from the database by IDs.
        An exception is thrown if there are items in the IDs that do not exist in the database.
        :param image_id: The list of IDs to retrieve.
        :param with_vectors: Whether to retrieve vectors.
        :return: The list of retrieved items.
        """
        logger.info("Retrieving {} items from database...", len(image_id))
        result = await self._client.retrieve(collection_name=self.collection_name,
                                             ids=image_id,
                                             with_payload=True,
                                             with_vectors=with_vectors)
        result_point_ids = {t.id for t in result}
        missing_point_ids = set(image_id) - result_point_ids
        if len(missing_point_ids) > 0:
            logger.error("{} points not exist.", len(missing_point_ids))
            raise PointNotFoundError(str(missing_point_ids))
        return self._get_mapped_image_from_point_batch(result)

    async def validate_ids(self, image_id: list[str]) -> list[str]:
        """
        Validate a list of IDs. Will return a list of valid IDs.
        :param image_id: The list of IDs to validate.
        :return: The list of valid IDs.
        """
        logger.info("Validating {} items from database...", len(image_id))
        result = await self._client.retrieve(collection_name=self.collection_name,
                                             ids=image_id,
                                             with_payload=False,
                                             with_vectors=False)
        return [t.id for t in result]

    @staticmethod
    def _convert_basis_to_qdrant_query(basis: DbQueryBasis):
        def map_criteria(criteria: DbQueryCriteria) -> str | list[float]:
            if isinstance(criteria, DbQueryCriteriaId):
                return criteria.id
            elif isinstance(criteria, DbQueryCriteriaVector):
                return criteria.vector
            else:
                raise ValueError(f"Invalid criteria type: {criteria.type}")

        if basis.negative or len(basis.positive) > 1:
            # RecommendQuery is required
            return RecommendQuery(
                recommend=RecommendInput(
                    positive=[map_criteria(t) for t in basis.positive],
                    negative=[map_criteria(t) for t in basis.negative],
                    strategy=RecommendStrategy.AVERAGE_VECTOR if basis.mix_strategy == SearchModelEnum.average
                    else RecommendStrategy.BEST_SCORE
                )
            )
        else:
            return NearestQuery(
                nearest=map_criteria(basis.positive[0]),
            )

    async def query_search(self, query: DbQuery, top_k=10, skip=0, filter_param: FilterParams | None = None) -> list[
        SearchResult]:
        """
        Query the database with a unified query object.
        :param query: The query object containing the query vector and basis.
        :param top_k: The number of results to return.
        :param skip: The number of results to skip.
        :param filter_param: Optional filter parameters to apply to the query.
        :return: A list of SearchResult objects.
        """
        logger.info("Starting unified search with {} criteria basis, top_k={}, skip={}",
                    len(query.criteria), top_k, skip)
        filters = self._get_filters_by_filter_param(filter_param)
        if len(query.criteria) > 1:
            # Hybrid search with RRF
            logger.info("Performing hybrid search with RRF fusion across {} criteria", len(query.criteria))
            prefetches = [Prefetch(
                query=self._convert_basis_to_qdrant_query(v),
                using=self.vector_name_for_basis(k),
                filter=filters,
                limit=(top_k + skip) * 2  # Increase limit to improve RRF fusion results
            ) for (k, v) in query.criteria.items()]

            result = await self._client.query_points(
                collection_name=self.collection_name,
                prefetch=prefetches,
                query=FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
                offset=skip,
                with_payload=True
            )
        else:
            # Normal search
            basis, criteria = next(iter(query.criteria.items()))
            logger.info("Performing normal search with basis {}", basis)
            result = await self._client.query_points(
                collection_name=self.collection_name,
                query=self._convert_basis_to_qdrant_query(criteria),
                using=self.vector_name_for_basis(basis),
                query_filter=filters,
                limit=top_k,
                offset=skip,
                with_payload=True
            )
        logger.success("Search completed! Found {} points.", len(result.points))
        return [self._get_search_result_from_scored_point(t) for t in result.points]

    async def insert_items(self, items: list[MappedImage]):
        logger.info("Inserting {} items into Qdrant...", len(items))

        points = [self._get_point_from_mapped_image(t) for t in items]

        response = await self._client.upsert(collection_name=self.collection_name,
                                             wait=True,
                                             points=points)
        logger.success("Insert completed! Status: {}", response.status)

    async def delete_items(self, ids: list[str]):
        logger.info("Deleting {} items from Qdrant...", len(ids))
        response = await self._client.delete(collection_name=self.collection_name,
                                             points_selector=models.PointIdsList(
                                                 points=ids
                                             ),
                                             )
        logger.success("Delete completed! Status: {}", response.status)

    async def update_payload(self, new_data: MappedImage):
        """
        Update the payload of an existing item in the database.
        Warning: This method will not update the vector of the item.
        :param new_data: The new data to update.
        """
        response = await self._client.set_payload(collection_name=self.collection_name,
                                                  payload=new_data.payload,
                                                  points=[str(new_data.id)],
                                                  wait=True)
        logger.success("Update completed! Status: {}", response.status)

    async def update_vectors(self, new_points: list[MappedImage]):
        resp = await self._client.update_vectors(collection_name=self.collection_name,
                                                 points=[self._get_vector_from_img_data(t) for t in new_points],
                                                 )
        logger.success("Update vectors completed! Status: {}", resp.status)

    async def scroll_points(self,
                            from_id: str | None = None,
                            count=50,
                            with_vectors=False,
                            filter_param: FilterParams | None = None,
                            ) -> tuple[list[MappedImage], str]:
        resp, next_id = await self._client.scroll(collection_name=self.collection_name,
                                                  limit=count,
                                                  offset=from_id,
                                                  with_vectors=with_vectors,
                                                  scroll_filter=self._get_filters_by_filter_param(filter_param)
                                                  )

        return [self._get_mapped_image_from_point(t) for t in resp], next_id

    async def get_counts(self, exact: bool) -> int:
        resp = await self._client.count(collection_name=self.collection_name, exact=exact)
        return resp.count

    async def check_collection(self) -> bool:
        resp = await self._client.get_collections()
        resp = [t.name for t in resp.collections]
        return self.collection_name in resp

    async def initialize_collection(self):
        if await self.check_collection():
            logger.warning("Collection already exists. Skip initialization.")
            return
        logger.info("Initializing database, collection name: {}", self.collection_name)
        vectors_config = {
            self.IMG_VECTOR: models.VectorParams(size=768, distance=models.Distance.COSINE),
            self.TEXT_VECTOR: models.VectorParams(size=768, distance=models.Distance.COSINE)
        }
        await self._client.create_collection(collection_name=self.collection_name,
                                             vectors_config=vectors_config)
        logger.success("Collection created!")

    @classmethod
    def _get_vector_from_img_data(cls, img_data: MappedImage) -> models.PointVectors:
        vector = {}
        if img_data.image_vector is not None:
            vector[cls.IMG_VECTOR] = img_data.image_vector.tolist()
        if img_data.text_contain_vector is not None:
            vector[cls.TEXT_VECTOR] = img_data.text_contain_vector.tolist()
        return models.PointVectors(
            id=str(img_data.id),
            vector=vector
        )

    @classmethod
    def _get_point_from_mapped_image(cls, img_data: MappedImage) -> models.PointStruct:
        return models.PointStruct(
            id=str(img_data.id),
            payload=img_data.payload,
            vector=cls._get_vector_from_img_data(img_data).vector
        )

    def _get_mapped_image_from_point(self, point: AVAILABLE_POINT_TYPES) -> MappedImage:
        return (MappedImage
                .from_payload(point.id,
                              point.payload,
                              image_vector=numpy.array(point.vector[self.IMG_VECTOR], dtype=numpy.float32)
                              if point.vector and self.IMG_VECTOR in point.vector else None,
                              text_contain_vector=numpy.array(point.vector[self.TEXT_VECTOR], dtype=numpy.float32)
                              if point.vector and self.TEXT_VECTOR in point.vector else None
                              ))

    def _get_mapped_image_from_point_batch(self, points: list[AVAILABLE_POINT_TYPES]) -> list[MappedImage]:
        return [self._get_mapped_image_from_point(t) for t in points]

    def _get_search_result_from_scored_point(self, point: models.ScoredPoint) -> SearchResult:
        return SearchResult(img=self._get_mapped_image_from_point(point), score=point.score)

    @classmethod
    def vector_name_for_basis(cls, basis: SearchBasisEnum) -> str:
        match basis:
            case SearchBasisEnum.vision:
                return cls.IMG_VECTOR
            case SearchBasisEnum.ocr:
                return cls.TEXT_VECTOR
            case _:
                raise ValueError("Invalid basis")

    @staticmethod
    def _get_filters_by_filter_param(filter_param: FilterParams | None) -> models.Filter | None:
        if filter_param is None:
            return None

        filters = []
        neg_filter = []
        if filter_param.min_width is not None and filter_param.min_width > 0:
            filters.append(models.FieldCondition(
                key="width",
                range=models.Range(
                    gte=filter_param.min_width
                )
            ))

        if filter_param.min_height is not None and filter_param.min_height > 0:
            filters.append(models.FieldCondition(
                key="height",
                range=models.Range(
                    gte=filter_param.min_height
                )
            ))

        if filter_param.min_ratio is not None:
            filters.append(models.FieldCondition(
                key="aspect_ratio",
                range=models.Range(
                    gte=filter_param.min_ratio,
                    lte=filter_param.max_ratio
                )
            ))

        if filter_param.starred is not None:
            filters.append(models.FieldCondition(
                key="starred",
                match=models.MatchValue(
                    value=filter_param.starred
                )
            ))

        if filter_param.ocr_text is not None:
            filters.append(models.FieldCondition(
                key="ocr_text_lower",
                match=models.MatchText(
                    text=filter_param.ocr_text.lower()
                )
            ))

        if filter_param.categories is not None:
            filters.append(models.FieldCondition(
                key="categories",
                match=models.MatchAny(
                    any=filter_param.categories
                )
            ))

        if filter_param.categories_negative is not None:
            neg_filter.append(models.FieldCondition(
                key="categories",
                match=models.MatchAny(any=filter_param.categories_negative),
            ))

        if not filters and not neg_filter:
            return None
        return models.Filter(
            must=filters,
            must_not=neg_filter
        )
