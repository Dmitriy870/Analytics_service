from uuid import UUID

from fastapi import APIRouter, Depends, Query

from analytics.dependencies import get_analytics_service
from analytics.exceptions import DocumentNotFound, DocumentNotFoundException
from analytics.schema import EventType
from analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/period")
async def get_period_stats(
    start_date: str = Query(..., description="Start date"),
    end_date: str = Query(..., description="End date"),
    field: str = Query(..., description="Field name"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.get_period_stats(start_date, end_date, field)


@router.get("/daily")
async def get_daily_stats(date: str, service: AnalyticsService = Depends(get_analytics_service)):
    try:
        return await service.get_daily_stats(date)
    except DocumentNotFound:
        raise DocumentNotFoundException


@router.get("/events")
async def get_events(
    user_id: UUID | None = Query(None, description="User id"),
    event_type: EventType | None = Query(None, description="Event type"),
    event_name: str | None = Query(None, description="Event name"),
    start_date: str | None = Query(None, description="Start date"),
    end_date: str | None = Query(None, description="End date"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Limit number"),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return await service.get_events(
        user_id, event_type, event_name, start_date, end_date, page, limit
    )
