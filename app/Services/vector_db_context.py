from typing import Optional

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


class PointNotFoundError(ValueError):
    def __init__(self, point_id: str):
        self.point_id = point_id
        super().__init__(f"Point {point_id} not found.")


class VectorDbContext:
    IMG_VECTOR = "image_vector"
    TEXT_VECTOR = "text_contain_vector"

    def __init__(self):
        self.client = AsyncQdrantClient(host=config.qdrant.host, port=config.qdrant.port,
                                        grpc_port=config.qdrant.grpc_port, api_key=config.qdrant.api_key,
                                        prefer_grpc=config.qdrant.prefer_grpc)
        self.collection_name = config.qdrant.coll

    async def retrieve_by_id(self, id: str, with_vectors=False) -> ImageData:
        logger.info("Retrieving item {} from database...", id)
        result = await self.client.retrieve(collection_name=self.collection_name, ids=[id], with_payload=True,
                                            with_vectors=with_vectors)
        if len(result) != 1:
            logger.error("Point not exist.")
            raise PointNotFoundError(id)
        return ImageData.from_payload(result[0].id, result[0].payload,
                                      numpy.array(result[0].vector, dtype=numpy.float32) if with_vectors else None)

    async def querySearch(self, query_vector, query_vector_name: str = IMG_VECTOR,
                          top_k=10, skip=0, filter_param: FilterParams | None = None) -> list[SearchResult]:
        logger.info("Querying Qdrant... top_k = {}", top_k)
        result = await self.client.search(collection_name=self.collection_name,
                                          query_vector=(query_vector_name, query_vector),
                                          query_filter=self.getFiltersByFilterParam(filter_param),
                                          limit=top_k,
                                          offset=skip,
                                          with_payload=True)
        logger.success("Query completed!")
        return [SearchResult(img=ImageData.from_payload(t.id, t.payload), score=t.score) for t in result]

    async def querySimilar(self,
                           query_vector_name: str = IMG_VECTOR,
                           search_id: Optional[str] = None,
                           positive_vectors: Optional[list[numpy.ndarray]] = None,
                           negative_vectors: Optional[list[numpy.ndarray]] = None,
                           mode: Optional[SearchModelEnum] = None,
                           with_vectors: bool = False,
                           filter_param: FilterParams | None = None,
                           top_k: int = 10,
                           skip: int = 0) -> list[SearchResult]:
        _positive_vectors = [t.tolist() for t in positive_vectors] if positive_vectors is not None else [search_id]
        _negative_vectors = [t.tolist() for t in negative_vectors] if negative_vectors is not None else None
        _strategy = None if mode is None else (RecommendStrategy.AVERAGE_VECTOR if
                                               mode == SearchModelEnum.average else RecommendStrategy.BEST_SCORE)
        # since only combined_search need return vectors, We can define _combined_search_need_vectors like below
        _combined_search_need_vectors = [self.IMG_VECTOR if query_vector_name == self.TEXT_VECTOR else self.IMG_VECTOR] \
            if with_vectors else None
        logger.info("Querying Qdrant... top_k = {}", top_k)
        result = await self.client.recommend(collection_name=self.collection_name,
                                             using=query_vector_name,
                                             positive=_positive_vectors,
                                             negative=_negative_vectors,
                                             strategy=_strategy,
                                             with_vectors=_combined_search_need_vectors,
                                             query_filter=self.getFiltersByFilterParam(filter_param),
                                             limit=top_k,
                                             offset=skip,
                                             with_payload=True)
        logger.success("Query completed!")

        def result_transform(t):
            return SearchResult(
                img=ImageData.from_payload(
                    t.id,
                    t.payload,
                    numpy.array(t.vector['image_vector']) if t.vector and 'image_vector' in t.vector else None,
                    numpy.array(
                        t.vector['text_contain_vector']) if t.vector and 'text_contain_vector' in t.vector else None
                ),
                score=t.score
            )

        return [result_transform(t) for t in result]

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

    async def deleteItems(self, ids: list[str]):
        logger.info("Deleting {} items from Qdrant...", len(ids))
        response = await self.client.delete(collection_name=self.collection_name,
                                            points_selector=models.PointIdsList(
                                                points=ids
                                            ),
                                            )
        logger.success("Delete completed! Status: {}", response.status)

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

        if len(filters) > 0:
            return models.Filter(
                must=filters
            )
        else:
            return None
