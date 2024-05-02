from qdrant_client import qdrant_client, models


def create_coll(host, port, name):
    client = qdrant_client.QdrantClient(host=host, port=port)
    # create or update
    print("Creating collection")
    vectors_config = {
        "image_vector": models.VectorParams(size=768, distance=models.Distance.COSINE),
        "text_contain_vector": models.VectorParams(size=768, distance=models.Distance.COSINE)
    }
    client.create_collection(collection_name=name,
                             vectors_config=vectors_config)
    print("Collection created")
