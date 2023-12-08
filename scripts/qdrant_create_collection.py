from qdrant_client import qdrant_client, models
import argparse


def parsing_args():
    parser = argparse.ArgumentParser(description='Create Qdrant collection')
    parser.add_argument('--host', type=str, required=False, default="127.0.0.1", help="Qdrant host")
    parser.add_argument('--port', type=int, required=False, default=6333, help="Qdrant port")
    parser.add_argument("--name", type=str, required=False, default="NekoImg", help="Collection name")
    # switch create or update
    parser.add_argument("--update", help="Update collection, if not provided - create new collection",
                        action="store_true")
    return parser.parse_args()


def create_coll(args):
    client = qdrant_client.QdrantClient(host=args.host, port=args.port)
    # create or update
    if args.update:
        print("Updating collection")
        client.update_collection(collection_name=args.name,
                                 vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
                                 )
    else:
        print("Creating collection")
        client.create_collection(collection_name=args.name,
                                 vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
                                 )
    print("Collection updated")


if __name__ == '__main__':
    args = parsing_args()
    create_coll(args)
