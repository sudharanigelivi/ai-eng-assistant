from datetime import datetime

from pydantic import BaseModel, Field


class CreateLinkRequest(BaseModel):
    url: str = Field(..., examples=["https://example.com/some/long/path?q=1"])
    custom_alias: str | None = Field(None, examples=["my-link"])
    expires_at: datetime | None = Field(None, description="Timezone-aware ISO-8601 timestamp")


class LinkResponse(BaseModel):
    code: str
    short_url: str
    url: str
    created_at: datetime
    expires_at: datetime | None
    click_count: int


class CountItem(BaseModel):
    name: str
    clicks: int


class DayItem(BaseModel):
    day: str
    clicks: int


class AnalyticsResponse(BaseModel):
    code: str
    total_clicks: int
    window_days: int
    clicks_in_window: int
    by_day: list[DayItem]
    top_referrers: list[CountItem]
    devices: list[CountItem]


class ErrorResponse(BaseModel):
    detail: str
