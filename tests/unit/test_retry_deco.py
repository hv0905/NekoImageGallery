import asyncio

import pytest

from app.util.retry_deco_async import retry_async, wrap_object


class TestRetryDeco:
    class ExampleClass:
        def __init__(self):
            self.counter = 0
            self.counter2 = 0
            self.not_func = 'not a function'

        async def example_method(self):
            await asyncio.sleep(0)
            self.counter += 1
            if self.counter < 3:
                raise ValueError("Counter is less than 3")
            return self.counter

        async def example_method_must_raise(self):
            await asyncio.sleep(0)
            self.counter2 += 1
            raise NotImplementedError("This method must raise an exception.")

    @pytest.mark.asyncio
    async def test_decorator(self):
        obj = self.ExampleClass()

        @retry_async(tries=3)
        def caller():
            return obj.example_method()

        assert await caller() == 3

    @pytest.mark.asyncio
    async def test_object_wrapper(self):
        obj = self.ExampleClass()
        wrap_object(obj, retry_async(ValueError, tries=2))
        assert isinstance(obj.not_func, str)
        with pytest.raises(ValueError):
            await obj.example_method()
        assert await obj.example_method() == 3
        with pytest.raises(NotImplementedError):
            await obj.example_method_must_raise()
        assert obj.counter2 == 1
