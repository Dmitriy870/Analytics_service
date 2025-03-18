import asyncio
import logging
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from analytics.kafka_consumer import consume_messages
from analytics.router import router
from analytics.schema import KafkaTopic
from config import VersionConfig
from database import MongoDB

logger = logging.getLogger(__name__)
version_config = VersionConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await MongoDB.connect()
    consumer_event_task = asyncio.create_task(consume_messages(KafkaTopic.EVENTS_TOPIC.value))
    consumer_model_task = asyncio.create_task(consume_messages(KafkaTopic.MODELS_TOPIC.value))
    try:
        yield
    finally:
        consumer_model_task.cancel()
        consumer_event_task.cancel()
        try:
            await consumer_model_task
        except asyncio.CancelledError:
            logger.info("Consumer task is cancelled")
        try:
            await consumer_event_task
        except asyncio.CancelledError:
            logger.info("Consumer task is cancelled")


class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid token"},
            )

        token = auth_header.split(" ")[1]
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{version_config.AUTH_SERVICE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                if response.status != 200:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Missing or invalid token"},
                    )
                result = await response.json()

        if result.get("role") != "admin":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Permission denied"}
            )

        response = await call_next(request)
        return response


app = FastAPI(lifespan=lifespan)


app.add_middleware(AdminAuthMiddleware)
app.include_router(router, prefix=version_config.API_V1_PREFIX)
