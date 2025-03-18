from contextlib import asynccontextmanager
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import MongoConfig

mongo_config = MongoConfig()


class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    @classmethod
    async def get_db(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            await cls.connect()
        return cls.db

    @classmethod
    async def connect(cls):
        cls.client = AsyncIOMotorClient(
            mongo_config.HOST, mongo_config.PORT, maxPoolSize=100, minPoolSize=10
        )
        cls.db = cls.client[mongo_config.DB]

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None


@asynccontextmanager
async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    try:
        db = await MongoDB.get_db()
        yield db
    finally:
        pass
