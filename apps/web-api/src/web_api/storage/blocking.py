"""Calling the async store from synchronous code, such as the worker."""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_blocking(operation: Coroutine[Any, Any, T]) -> T:
    """Run one store operation to completion from code that has no event loop."""
    return asyncio.run(operation)
