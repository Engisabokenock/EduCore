from pydantic import BaseModel, ConfigDict
from enum import Enum

class ChartInterval(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class TimeseriesDataPoint(BaseModel):
    label: str  # Format: "YYYY-MM-DD", "Week 24", "Jan 2026", or "2026"
    value: float

class KeyMetricSummary(BaseModel):
    total_downloads: int
    total_revenue: float
    total_users: int
    premium_sales_count: int

class RankedSubjectMetric(BaseModel):
    subject_id: str
    subject_name: str
    grade_name: str
    download_count: int

class RankedTopicMetric(BaseModel):
    topic_id: str
    topic_name: str
    subject_name: str
    download_count: int

class TrafficSummaryMetrics(BaseModel):
    total_hits: int
    unique_devices_count: int
    timeseries: list[TimeseriesDataPoint]

class ComprehensiveDashboardPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    summary: KeyMetricSummary
    revenue_chart: list[TimeseriesDataPoint]
    downloads_chart: list[TimeseriesDataPoint]
    top_subjects: list[RankedSubjectMetric]
    top_topics: list[RankedTopicMetric]
