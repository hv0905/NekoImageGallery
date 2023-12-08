from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct, Batch

import app.config as config
from app.Models.img_data import ImageData
from app.Models.search_result import SearchResult


class VectorDbContext:
    def __init__(self):
        self.client = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        self.collection_name = config.QDRANT_COLL

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

    async def insertItems(self, items: list[ImageData]):
        logger.info("Inserting {} items into Qdrant...", len(items))
        points = [PointStruct(id=str(t.id), vector=t.image_vector.tolist(), payload=t.payload) for t in items]
        response = await self.client.upsert(collection_name=self.collection_name,
                                            wait=True,
                                            points=points)
        logger.success("Insert completed! Status: {}", response.status)

