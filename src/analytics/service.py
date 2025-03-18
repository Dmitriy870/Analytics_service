import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from analytics.exceptions import DocumentNotFound, InvalidDate
from analytics.schema import Event, EventType, PeriodResponse

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.events = db.events
        self.daily_stats = db.daily_stats

    @staticmethod
    def is_valid_interval(start_date: str, end_date: str) -> bool:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise InvalidDate("Invalid date format")
        return end_dt >= start_dt

    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def convert_uuid_to_str(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
            elif isinstance(value, dict):
                data[key] = self.convert_uuid_to_str(value)
            elif isinstance(value, list):
                data[key] = [
                    self.convert_uuid_to_str(item) if isinstance(item, dict) else item
                    for item in value
                ]
        return data

    async def process_event(self, event_data: dict) -> None:
        logger.info("Processing event(before event create)")
        event_data = self.convert_uuid_to_str(event_data)
        logger.info("Processing event(after convert)")
        event = Event(**event_data)
        await self.save_event(event)

        if event.event_type == EventType.EVENT:
            await self.update_daily_stats(event.received_at, "events_count")
        elif event.event_type == EventType.MODEL:
            await self.process_model_event(event)

    async def save_event(self, event: Event) -> None:
        logger.info("Saving event(after event create)")
        await self.events.insert_one(event.model_dump(by_alias=True))
        logger.info("succesfully saved event(after event create)")

    async def process_model_event(self, event: Event) -> None:
        if event.event_name.startswith("get_"):
            await self.update_daily_stats(event.received_at, f"{event.model_type}_get_count")
        if event.event_name.startswith("create_"):
            await self.update_daily_stats(event.received_at, f"{event.model_type}_created_count")
        elif event.event_name.startswith("update_"):
            await self.update_daily_stats(event.received_at, f"{event.model_type}_updated_count")
        elif event.event_name.startswith("delete_"):
            await self.update_daily_stats(event.received_at, f"{event.model_type}_deleted_count")

    async def update_daily_stats(self, dt: datetime, field: str, increment: int = 1) -> None:
        date_str = dt.strftime("%Y-%m-%d")
        await self.daily_stats.update_one(
            {"date": date_str}, {"$inc": {field: increment}}, upsert=True
        )

    async def get_period_stats(self, start_date: str, end_date: str, field: str):
        if not self.is_valid_interval(start_date, end_date):
            raise InvalidDate("Invalid date interval")
        stats = []
        async for doc in self.daily_stats.find(
            {"date": {"$gte": start_date, "$lte": end_date}},
            {"_id": False, "date": True, field: True},
        ):
            stats.append(PeriodResponse(date=doc["date"], field=doc.get(field)))

        return stats

    async def get_daily_stats(self, date: str):
        if not self.is_valid_date(date):
            raise InvalidDate("Invalid date or date format")

        doc = await self.daily_stats.find_one({"date": date}, {"_id": False})
        if not doc:
            raise DocumentNotFound("Document not found")

        return doc

    async def get_events(
        self,
        user_id: UUID | None = None,
        event_type: EventType | None = None,
        event_name: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> list[Event]:
        filter_query: dict[str, Any] = {}

        if user_id:
            filter_query["user_id"] = str(user_id)
        if event_type:
            filter_query["event_type"] = event_type
        if event_name is not None:
            # filter_query["event_name"] = {"$regex": f"^{event_name}"}
            filter_query["event_name"] = event_name
        if start_date and not self.is_valid_date(start_date):
            raise ValueError("Invalid start_date format")
        if end_date and not self.is_valid_date(end_date):
            raise ValueError("Invalid end_date format")
        if start_date and end_date:
            filter_query["received_at"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            filter_query["received_at"] = {"$gte": start_date}
        elif end_date:
            filter_query["received_at"] = {"$lte": end_date}

        skip = (page - 1) * limit
        cursor = self.events.find(filter_query).sort("received_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [Event(**doc) for doc in docs]
