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
    parser.add_argument('--local-create-thumbnail', action='store_true',
                        help='Create thumbnail for all local images in static folder set in config.py. When this flag '
                             'is set, will not start the server.')
    parser.add_argument('--port', type=int, default=8000, help="Port to listen on, default is 8000")
    parser.add_argument('--host', type=str, default="0.0.0.0", help="Host to bind on, default is 0.0.0.0")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.init_database:
        from scripts import qdrant_create_collection
        from app.config import config

        qdrant_create_collection.create_coll(
            collections.namedtuple('Options', ['host', 'port', 'name'])(config.qdrant.host, config.qdrant.port,
                                                                        config.qdrant.coll))
    elif args.local_index_target_dir is not None:
        from scripts import local_indexing
        import asyncio

        asyncio.run(local_indexing.main(args))
    elif args.local_create_thumbnail:
        from scripts import local_create_thumbnail
        import asyncio

        asyncio.run(local_create_thumbnail.main())
    else:
        uvicorn.run("app.webapp:app", host=args.host, port=args.port)
