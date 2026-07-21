"""Shared Pydantic base for API resource models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Py2KModel(BaseModel):
    """Accepts the API's camelCase fields via snake_case attrs.

    `extra="allow"` because the API exposes 40+ dynamic attribute/badge
    fields we don't want to hard-fail on if the upstream schema adds more.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )