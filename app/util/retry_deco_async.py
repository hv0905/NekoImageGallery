import asyncio
import functools
from typing import Callable

from loguru import logger


def retry_async(exceptions=Exception, tries=3, delay=0) -> Callable[[Callable], Callable]:
    def deco_retry(f):
        @functools.wraps(f)
        async def f_retry(*args, **kwargs):
            m_tries, m_delay = tries, delay
            while m_tries > 1:
                try:
                    return await f(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"{e}, Retrying in {m_delay} seconds...")
                    if m_delay > 0:
                        await asyncio.sleep(m_delay)
                    m_tries -= 1
            return await f(*args, **kwargs)

        return f_retry

    return deco_retry


def wrap_object(obj: object, deco: Callable[[Callable], Callable]):
    for attr in dir(obj):
        if not attr.startswith('_') and asyncio.iscoroutinefunction(attr_val := getattr(obj, attr)):
            setattr(obj, attr, deco(attr_val))
