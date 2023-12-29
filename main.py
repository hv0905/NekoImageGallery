import argparse
import asyncio
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
    parser.add_argument('--migrate-db', dest="migrate_from_version", type=int,
                        help="Migrate qdrant database using connection settings in config from version specified."
                             "When this flag is set, will not start the server.")
    parser.add_argument('--local-index', dest="local_index_target_dir", type=str,
                        help="Index all the images in this directory and copy them to "
                             "static folder set in config.py. When this flag is set, "
                             "will not start the server.")
    parser.add_argument('--local-create-thumbnail', action='store_true',
                        help='Create thumbnail for all local images in static folder set in config.py. When this flag '
                             'is set, will not start the server.')
    parser.add_argument('--port', type=int, default=8000, help="Port to listen on, default is 8000")
    parser.add_argument('--host', type=str, default="0.0.0.0", help="Host to bind on, default is 0.0.0.0")
    parser.add_argument('--root-path', type=str, default="",
                        help="Root path of the server if your server is deployed behind a reverse proxy. "
                             "See https://fastapi.tiangolo.com/advanced/behind-a-proxy/ for detail.")

    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.init_database:
        from scripts import qdrant_create_collection
        from app.config import config

        qdrant_create_collection.create_coll(
            collections.namedtuple('Options', ['host', 'port', 'name'])(config.qdrant.host, config.qdrant.port,
                                                                        config.qdrant.coll))
    elif args.migrate_from_version is not None:
        from scripts import db_migrations

        asyncio.run(db_migrations.migrate(args.migrate_from_version))
    elif args.local_index_target_dir is not None:
        from app.config import environment

        environment.local_indexing = True
        from scripts import local_indexing

        asyncio.run(local_indexing.main(args))
    elif args.local_create_thumbnail:
        from scripts import local_create_thumbnail

        asyncio.run(local_create_thumbnail.main())
    else:
        uvicorn.run("app.webapp:app", host=args.host, port=args.port, root_path=args.root_path)
