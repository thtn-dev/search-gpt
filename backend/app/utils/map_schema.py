# pylint: disable=C0103
"""Mapping utility for converting SQLModel instances to Pydantic schemas."""

from typing import TypeVar

from pydantic import BaseModel
from sqlmodel import SQLModel

TSchema = TypeVar('TSchema', bound=BaseModel)
TModel = TypeVar('TModel', bound=SQLModel)


def map_models_schema(schema: BaseModel, models: list[TModel]):
    """
    Map SQLModel to Pydantic schema.
    """
    return [schema.model_validate(model) for model in models]
