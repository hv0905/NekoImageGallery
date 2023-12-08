import argparse
import collections

import uvicorn


def parse_args():
    parser = argparse.ArgumentParser(prog="NekoImageGallery Server",
                                     description='Ciallo~ Welcome to NekoImageGallery Server.',
                                     epilog="Build with ♥ By EdgeNeko. Github: "
                                            "https://github.com/hv0905/NekoImageGallery")
    parser.add_argument('--init-database', action='store_true',
                        help="Initialize qdrant database using connection settings in "
                             "config.py. When this flag is set, will not"
                             "start the server.")
    parser.add_argument('--local-index', dest="local_index_target_dir", type=str,
                        help="Index all the images in this directory and copy them to "
                             "static folder set in config.py. When this flag is set, "
                             "will not start the server.")
    parser.add_argument('--port', type=int, default=8000, help="Port to listen on, default is 8000")
    parser.add_argument('--host', type=str, default="0.0.0.0", help="Host to bind on, default is 0.0.0.0")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.init_database:
        from scripts import qdrant_create_collection
        import app.config as config

        qdrant_create_collection.create_coll(
            collections.namedtuple('Options', ['host', 'port', 'name'])(config.QDRANT_HOST, config.QDRANT_PORT,
                                                                        config.QDRANT_COLL))
    elif args.local_index_target_dir is not None:
        from scripts import local_indexing
        import asyncio
        asyncio.run(local_indexing.main(args))
    else:
        uvicorn.run("app.webapp:app", host=args.host, port=args.port)
