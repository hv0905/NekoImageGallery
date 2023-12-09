import numpy
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct, Batch

import app.config as config
from app.Models.img_data import ImageData
from app.Models.search_result import SearchResult


class VectorDbContext:
    def __init__(self):
        self.client = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT,
                                        grpc_port=config.QDRANT_GRPC_PORT, api_key=config.QDRANT_API_KEY,
                                        prefer_grpc=config.QDRANT_PREFER_GRPC)
        self.collection_name = config.QDRANT_COLL

    async def retrieve_by_id(self, id: str, with_vectors=False) -> ImageData:
        result = await self.client.retrieve(collection_name=self.collection_name, ids=[id], with_payload=True,
                                            with_vectors=with_vectors)
        return ImageData.from_payload(result[0].id, result[0].payload,
                                      numpy.ndarray(result[0].vector) if with_vectors else None)

    async def querySearch(self, query_vector, top_k=10) -> list[SearchResult]:
        logger.info("Querying Qdrant... top_k = {}", top_k)
        result = await self.client.search(collection_name=self.collection_name,
                                          query_vector=query_vector,
                                          limit=top_k,
                                          with_vectors=False,
                                          with_payload=True
                                          )
        logger.success("Query completed!")
        return [SearchResult(img=ImageData.from_payload(t.id, t.payload), score=t.score) for t in result]

    async def querySimilar(self, id: str, top_k=10) -> list[SearchResult]:
        logger.info("Querying Qdrant... top_k = {}", top_k)
        result = await self.client.recommend(collection_name=self.collection_name,
                                             positive=[id],
                                             negative=[],
                                             limit=top_k,
                                             with_vectors=False,
                                             with_payload=True,
                                             )
        logger.success("Query completed!")
        return [SearchResult(img=ImageData.from_payload(t.id, t.payload), score=t.score) for t in result]

    async def insertItems(self, items: list[ImageData]):
        logger.info("Inserting {} items into Qdrant...", len(items))
        points = [PointStruct(id=str(t.id), vector=t.image_vector.tolist(), payload=t.payload) for t in items]
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
                                      points=[new_data.id],
                                      wait=True
                                      )
        logger.success("Update completed! Status: {}", response.status)
