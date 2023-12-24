import numpy
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct
from qdrant_client.models import RecommendStrategy

from app.Models.api_model import SearchModelEnum, SearchBasisEnum
from app.Models.img_data import ImageData
from app.Models.query_params import FilterParams
from app.Models.search_result import SearchResult
from app.config import config


class VectorDbContext:
    IMG_VECTOR = "image_vector"
    TEXT_VECTOR = "text_contain_vector"

    def __init__(self):
        self.client = AsyncQdrantClient(host=config.qdrant.host, port=config.qdrant.port,
                                        grpc_port=config.qdrant.grpc_port, api_key=config.qdrant.api_key,
                                        prefer_grpc=config.qdrant.prefer_grpc)
        self.collection_name = config.qdrant.coll

    async def retrieve_by_id(self, id: str, with_vectors=False) -> ImageData:
        result = await self.client.retrieve(collection_name=self.collection_name, ids=[id], with_payload=True,
                                            with_vectors=with_vectors)
        return ImageData.from_payload(result[0].id, result[0].payload,
                                      numpy.array(result[0].vector, dtype=numpy.float32) if with_vectors else None)

    async def querySearch(self, query_vector, query_vector_name: str = IMG_VECTOR,
                          top_k=10, skip=0, filter_param: FilterParams | None = None) -> list[
        SearchResult]:
        logger.info("Querying Qdrant... top_k = {}", top_k)
        result = await self.client.search(collection_name=self.collection_name,
                                          query_vector=(query_vector_name, query_vector),
                                          query_filter=self.getFiltersByFilterParam(filter_param),
                                          limit=top_k,
                                          offset=skip,
                                          with_payload=True)
        logger.success("Query completed!")
        return [SearchResult(img=ImageData.from_payload(t.id, t.payload), score=t.score) for t in result]

    async def querySimilar(self, id: str, query_vector_name: str = IMG_VECTOR,
                           top_k=10, skip=0, filter_param: FilterParams | None = None) -> list[SearchResult]:
        logger.info("Querying Qdrant... top_k = {}", top_k)
        result = await self.client.recommend(collection_name=self.collection_name,
                                             positive=[id],
                                             negative=[],
                                             using=query_vector_name,
                                             query_filter=self.getFiltersByFilterParam(filter_param),
                                             limit=top_k,
                                             offset=skip,
                                             with_vectors=False,
                                             with_payload=True)
        logger.success("Query completed!")
        return [SearchResult(img=ImageData.from_payload(t.id, t.payload), score=t.score) for t in result]

    async def queryAdvanced(self, positive_vectors: list[numpy.ndarray], negative_vectors: list[numpy.ndarray],
                            query_vector_name: str = IMG_VECTOR, mode: SearchModelEnum = SearchModelEnum.average,
                            top_k=10, skip=0, filter_param: FilterParams | None = None) -> list[SearchResult]:
        logger.info("Querying Qdrant... top_k = {}", top_k)
        result = await self.client.recommend(collection_name=self.collection_name,
                                             using=query_vector_name,
                                             positive=[t.tolist() for t in positive_vectors],
                                             negative=[t.tolist() for t in negative_vectors],
                                             query_filter=self.getFiltersByFilterParam(filter_param),
                                             limit=top_k,
                                             offset=skip,
                                             strategy=
                                             (RecommendStrategy.AVERAGE_VECTOR if
                                              mode == SearchModelEnum.average else RecommendStrategy.BEST_SCORE),
                                             with_vectors=False,
                                             with_payload=True)
        logger.success("Query completed!")
        return [SearchResult(img=ImageData.from_payload(t.id, t.payload), score=t.score) for t in result]

    async def insertItems(self, items: list[ImageData]):
        logger.info("Inserting {} items into Qdrant...", len(items))

        def getPoint(img_data):
            vector = {
                self.IMG_VECTOR: img_data.image_vector.tolist(),
            }
            if img_data.text_contain_vector is not None:
                vector[self.TEXT_VECTOR] = img_data.text_contain_vector.tolist()
            return PointStruct(
                id=str(img_data.id),
                vector=vector,
                payload=img_data.payload
            )

        points = [getPoint(t) for t in items]

        response = await self.client.upsert(collection_name=self.collection_name,
                                            wait=True,
                                            points=points)
        logger.success("Insert completed! Status: {}", response.status)

    async def updatePayload(self, new_data: ImageData):
        """
        Update the payload of an existing item in the database.
        Warning: This method will not update the vector of the item.
        :param new_data: The new data to update.
        """
        response = await self.client.set_payload(collection_name=self.collection_name,
                                                 payload=new_data.payload,
                                                 points=[str(new_data.id)],
                                                 wait=True)
        logger.success("Update completed! Status: {}", response.status)

    @classmethod
    def getVectorByBasis(cls, basis: SearchBasisEnum) -> str:
        match basis:
            case SearchBasisEnum.vision:
                return cls.IMG_VECTOR
            case SearchBasisEnum.ocr:
                return cls.TEXT_VECTOR
            case _:
                raise ValueError("Invalid basis")

    @staticmethod
    def getFiltersByFilterParam(filter_param: FilterParams | None) -> models.Filter | None:
        if filter_param is None:
            return None

        filters = []
        if filter_param.min_width is not None:
            filters.append(models.FieldCondition(
                key="width",
                range=models.Range(
                    gte=filter_param.min_width
                )
            ))

        if filter_param.min_height is not None:
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

        if len(filters) > 0:
            return models.Filter(
                must=filters
            )
        else:
            return None
