from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class MongoConfig(BaseSettings):

    HOST: str = Field(...)
    PORT: int = Field(...)
    DB: str = Field(...)

    class Config:
        env_prefix = "MONGO_"


class KafkaConfig(BaseSettings):
    BOOTSTRAP_SERVERS: str = Field(...)
    GROUP_ID: str = Field(...)
    AUTO_OFFSET_RESET: str = Field(default="latest")
    ENABLE_AUTO_COMMIT: bool = Field(default=True)
    TOPICS: List[str] = Field(default=["models_topic", "events_topic"])

    class Config:
        env_prefix = "KAFKA_"


class VersionConfig(BaseSettings):
    API_V1_PREFIX: str = Field(default="/api/v1")
    AUTH_SERVICE_URL: str = Field(default="http://auth_app:8000/api/v1/auth")
