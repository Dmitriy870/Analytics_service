from datetime import datetime
from enum import Enum
from typing import Any, Dict

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):  # Добавлен третий параметр
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema):
        schema.update(type="string")


class KafkaTopic(str, Enum):
    MODELS_TOPIC = "models_topic"
    EVENTS_TOPIC = "events_topic"


class EventType(str, Enum):
    MODEL = "MODEL"
    EVENT = "EVENT"


class Event(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    event_type: EventType = Field(...)
    event_name: str = Field(...)
    received_from: str = Field(...)
    model_type: str | None = Field(None)
    model_data: Dict[str, Any] | None = Field(None)
    entity_id: str | None = Field(None)
    received_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class PeriodResponse(BaseModel):
    field: str | None = None
    date: int | None = None
