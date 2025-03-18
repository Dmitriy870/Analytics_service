from analytics.service import AnalyticsService
from database import MongoDB


async def get_analytics_service() -> AnalyticsService:
    db = await MongoDB.get_db()
    return AnalyticsService(db)
