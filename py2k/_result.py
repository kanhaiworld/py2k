"""Result list wrapper with pagination metadata and optional pandas export."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ResultList(list[T], Generic[T]):
    """A list of models plus the API's `meta` block (pagination, search stats)."""

    def __init__(self, items: list[T], meta: dict[str, Any] | None = None) -> None:
        super().__init__(items)
        self.meta = meta or {}

    @property
    def next_cursor(self) -> str | None:
        return self.meta.get("pagination", {}).get("nextCursor")

    @property
    def total(self) -> int | None:
        return self.meta.get("pagination", {}).get("total", self.meta.get("total"))

    def to_dataframe(self):
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "pandas is required for to_dataframe(); install with `pip install py2k[dataframe]`"
            ) from exc
        return pd.DataFrame([item.model_dump() for item in self])
