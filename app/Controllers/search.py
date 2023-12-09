from fastapi import APIRouter
from fastapi.params import Form, File, Query, Path
from loguru import logger
from typing import Annotated
from app.Services import clip_service
from app.Services import db_context
from PIL import Image
from io import BytesIO

searchRouter = APIRouter()


@searchRouter.get("/text/{prompt}")
async def textSearch(
        prompt: Annotated[str, Path(min_length=3, max_length=100, description="The image prompt text you want to search.")],
        count: Annotated[int, Query(ge=1, le=50, description="The number of results you want to get.")] = 10):
    """
    Search images by text prompt
    """
    logger.info("Text search request received, prompt: {}", prompt)
    text_vector = clip_service.get_text_vector(prompt)
    results = await db_context.querySearch(text_vector, top_k=count)
    return results


@searchRouter.post("/image")
async def imageSearch(image: Annotated[bytes, File(max_length=3 * 1024 * 1024, media_type="image/*", description="The image you want to search.")],
                      count: Annotated[int, Query(ge=1, le=50, description="The number of results you want to get.")] = 10):
    """
    Search images by image
    :param image:
    :param count:
    :return:
    """
    fakefile = BytesIO(image)
    img = Image.open(fakefile)
    logger.info("Image search request received")
    image_vector = clip_service.get_image_vector(img)
    results = await db_context.querySearch(image_vector, top_k=count)
    return results
