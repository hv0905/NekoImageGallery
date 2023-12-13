from qdrant_client import qdrant_client, models
import argparse


def parsing_args():
    parser = argparse.ArgumentParser(description='Create Qdrant collection')
    parser.add_argument('--host', type=str, required=False, default="127.0.0.1", help="Qdrant host")
    parser.add_argument('--port', type=int, required=False, default=6333, help="Qdrant port")
    parser.add_argument("--name", type=str, required=False, default="NekoImg", help="Collection name")
    return parser.parse_args()


def create_coll(args):
    client = qdrant_client.QdrantClient(host=args.host, port=args.port)
    # create or update
    print("Creating collection")
    vectors_config = {
        "image_vector": models.VectorParams(size=768, distance=models.Distance.COSINE),
        "text_contain_vector": models.VectorParams(size=768, distance=models.Distance.COSINE)
    }
    client.create_collection(collection_name=args.name,
                             vectors_config=vectors_config)
    print("Collection created")


if __name__ == '__main__':
    args = parsing_args()
    create_coll(args)
