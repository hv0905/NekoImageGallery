import asyncio
from pathlib import Path
from typing import Annotated, Optional

import rich
import typer
import uvicorn

import app

parser = typer.Typer(name=app.__title__,
                     epilog="Build with ♥ By EdgeNeko. Github: "
                            "https://github.com/hv0905/NekoImageGallery",
                     rich_markup_mode='markdown'
                     )


def version_callback(value: bool):
    if value:
        print(f"{app.__title__} v{app.__version__}")
        raise typer.Exit()


@parser.callback(invoke_without_command=True)
def server(ctx: typer.Context,
           host: Annotated[str, typer.Option(help='The host to bind on.')] = '0.0.0.0',
           port: Annotated[int, typer.Option(help='The port to listen on.')] = 8000,
           root_path: Annotated[str, typer.Option(
               help='Root path of the server if your server is deployed behind a reverse proxy. See '
                    'https://fastapi.tiangolo.com/advanced/behind-a-proxy/ for detail.')] = '',
           _: Annotated[
               Optional[bool], typer.Option("--version", callback=version_callback, is_eager=True,
                                            help="Show version and exit.")
           ] = None
           ):
    """
    Ciallo~ Welcome to NekoImageGallery Server.

    - Website: https://image-insights.edgneko.com

    - Repository & Issue tracker: https://github.com/hv0905/NekoImageGallery



    By default, running without command will start the server.
    You can perform other actions by using the commands below.
    """
    if ctx.invoked_subcommand is not None:
        return
    uvicorn.run("app.webapp:app", host=host, port=port, root_path=root_path)


@parser.command('show-config')
def show_config():
    """
    Print the current configuration and exit.
    """
    from app.config import config
    rich.print_json(config.model_dump_json())


@parser.command('init-database')
def init_database():
    """
    Initialize qdrant database using connection settings in configuration.
    Note. The server will automatically initialize the database if it's not initialized. So you don't need to run this
    command unless you want to explicitly initialize the database.
    """
    from scripts import qdrant_create_collection
    asyncio.run(qdrant_create_collection.main())


@parser.command("local-index")
def local_index(
        target_dir: Annotated[
            list[Path], typer.Argument(dir_okay=True, file_okay=False, exists=True, resolve_path=True, readable=True,
                                       help="Directories you want to index.")],
        categories: Annotated[Optional[list[str]], typer.Option(help="Categories for the indexed images.")] = None,
        starred: Annotated[bool, typer.Option(help="Whether the indexed images are starred.")] = False,
):
    """
    Index all the images in the specified directory.
    The images will be copied to the local storage directory set in configuration.
    """
    from scripts import local_indexing
    if categories is None:
        categories = []
    asyncio.run(local_indexing.main(target_dir, categories, starred))


@parser.command('local-create-thumbnail', deprecated=True)
def local_create_thumbnail():
    """
    Create thumbnail for all local images in static folder, this won't affect non-local images.
    This is generally not required since the server will automatically create thumbnails for new images by default.
    This option will be refactored in the future.
    """
    from scripts import local_create_thumbnail
    asyncio.run(local_create_thumbnail.main())


if __name__ == '__main__':
    parser()
