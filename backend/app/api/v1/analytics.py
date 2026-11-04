from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, desc, cast, String
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.deps import RoleChecker
from app.models.base import User, UserRole
from app.models.resource import AcademicResource
from app.models.cbc import Subject, Topic, Grade
from app.models.tracking import DownloadLog
from app.models.payment import PaymentTransaction, TransactionStatus
from app.schemas.analytics import (
    ChartInterval, ComprehensiveDashboardPayload, TimeseriesDataPoint,
    KeyMetricSummary, RankedSubjectMetric, RankedTopicMetric, TrafficSummaryMetrics
)

router = APIRouter(prefix="/analytics", tags=["Operational Intelligence & Dashboard Aggregations"])

# Restrict the analytical calculation routes strictly to administrative systems
admin_protect = Depends(RoleChecker([UserRole.ADMIN]))

def get_interval_trunc_expression(column, interval: ChartInterval):
    """Compiles the target SQL date grouping sub-string slice matching targeted granular periods."""
    if interval == ChartInterval.DAILY:
        return func.to_char(column, "YYYY-MM-DD")
    elif interval == ChartInterval.WEEKLY:
        return func.concat(func.to_char(column, "YYYY-W"), func.to_char(column, "IW"))
    elif interval == ChartInterval.MONTHLY:
        return func.to_char(column, "YYYY-MM")
    elif interval == ChartInterval.YEARLY:
        return func.to_char(column, "YYYY")
    return func.to_char(column, "YYYY-MM-DD")

@router.get("/dashboard", response_model=ComprehensiveDashboardPayload, dependencies=[admin_protect])
async def fetch_comprehensive_admin_dashboard(
    interval: ChartInterval = Query(ChartInterval.MONTHLY),
    days_back: int = Query(365, ge=7, le=1095),
    db: AsyncSession = Depends(get_db)
):
    """
    Asynchronously calculates real-time metrics, time-series data vectors,
    and curriculum interactions across all storage partitions.
    """
    now_utc = datetime.now(timezone.utc)
    start_timeline_filter = now_utc - timedelta(days=days_back)

    # -------------------------------------------------------------------------
    # 1. UPPER ROW SUMMARY COUNTERS PIPELINE
    # -------------------------------------------------------------------------
    total_downloads_stmt = select(func.count(DownloadLog.id))
    downloads_execution = await db.execute(total_downloads_stmt)
    total_downloads = downloads_execution.scalar() or 0

    total_revenue_stmt = select(func.sum(PaymentTransaction.amount)).where(
        PaymentTransaction.status == TransactionStatus.COMPLETED
    )
    revenue_execution = await db.execute(total_revenue_stmt)
    total_revenue = float(revenue_execution.scalar() or 0.0)

    total_users_stmt = select(func.count(User.id))
    users_execution = await db.execute(total_users_stmt)
    total_users = users_execution.scalar() or 0

    premium_sales_stmt = select(func.count(PaymentTransaction.id)).where(
        and_(
            PaymentTransaction.status == TransactionStatus.COMPLETED,
            PaymentTransaction.amount > 0
        )
    )
    premium_sales_execution = await db.execute(premium_sales_stmt)
    premium_sales_count = premium_sales_execution.scalar() or 0

    summary_metrics = KeyMetricSummary(
        total_downloads=total_downloads,
        total_revenue=total_revenue,
        total_users=total_users,
        premium_sales_count=premium_sales_count
    )

    # -------------------------------------------------------------------------
    # 2. REVENUE CHANNELS TIMESERIES DATA PIPELINE
    # -------------------------------------------------------------------------
    rev_trunc = get_interval_trunc_expression(PaymentTransaction.created_at, interval)
    revenue_chart_stmt = (
        select(rev_trunc.label("period"), func.sum(PaymentTransaction.amount).label("value"))
        .where(
            and_(
                PaymentTransaction.status == TransactionStatus.COMPLETED,
                PaymentTransaction.created_at >= start_timeline_filter
            )
        )
        .group_by("period")
        .order_by("period")
    )
    revenue_chart_ctx = await db.execute(revenue_chart_stmt)
    revenue_chart_points = [
        TimeseriesDataPoint(label=row.period, value=float(row.value or 0.0))
        for row in revenue_chart_ctx.all()
    ]

    # -------------------------------------------------------------------------
    # 3. DOWNLOAD ACTIONS TIMESERIES DATA PIPELINE
    # -------------------------------------------------------------------------
    dl_trunc = get_interval_trunc_expression(DownloadLog.downloaded_at, interval)
    downloads_chart_stmt = (
        select(dl_trunc.label("period"), func.count(DownloadLog.id).label("value"))
        .where(DownloadLog.downloaded_at >= start_timeline_filter)
        .group_by("period")
        .order_by("period")
    )
    downloads_chart_ctx = await db.execute(downloads_chart_stmt)
    downloads_chart_points = [
        TimeseriesDataPoint(label=row.period, value=float(row.value or 0))
        for row in downloads_chart_ctx.all()
    ]

    # -------------------------------------------------------------------------
    # 4. MOST POPULAR SUBJECTS CORRELATION ANALYSIS (TOP 5)
    # -------------------------------------------------------------------------
    top_subjects_stmt = (
        select(
            cast(Subject.id, String).label("subject_id"),
            Subject.name.label("subject_name"),
            Grade.name.label("grade_name"),
            func.count(DownloadLog.id).label("download_count")
        )
        .join(AcademicResource, DownloadLog.resource_id == AcademicResource.id)
        .join(Subject, AcademicResource.subject_id == Subject.id)
        .join(Grade, Subject.grade_id == Grade.id)
        .group_by(Subject.id, Subject.name, Grade.name)
        .order_by(desc("download_count"))
        .limit(5)
    )
    top_subjects_ctx = await db.execute(top_subjects_stmt)
    popular_subjects_ranking = [
        RankedSubjectMetric(
            subject_id=row.subject_id,
            subject_name=row.subject_name,
            grade_name=row.grade_name,
            download_count=row.download_count
        )
        for row in top_subjects_ctx.all()
    ]

    # -------------------------------------------------------------------------
    # 5. MOST POPULAR TOPICS CORRELATION ANALYSIS (TOP 5)
    # -------------------------------------------------------------------------
    top_topics_stmt = (
        select(
            cast(Topic.id, String).label("topic_id"),
            Topic.name.label("topic_name"),
            Subject.name.label("subject_name"),
            func.count(DownloadLog.id).label("download_count")
        )
        .join(AcademicResource, DownloadLog.resource_id == AcademicResource.id)
        .join(Topic, AcademicResource.topic_id == Topic.id)
        .join(Subject, Topic.subject_id == Subject.id)
        .group_by(Topic.id, Topic.name, Subject.name)
        .order_by(desc("download_count"))
        .limit(5)
    )
    top_topics_ctx = await db.execute(top_topics_stmt)
    popular_topics_ranking = [
        RankedTopicMetric(
            topic_id=row.topic_id,
            topic_name=row.topic_name,
            subject_name=row.subject_name,
            download_count=row.download_count
        )
        for row in top_topics_ctx.all()
    ]

    return ComprehensiveDashboardPayload(
        summary=summary_metrics,
        revenue_chart=revenue_chart_points,
        downloads_chart=downloads_chart_points,
        top_subjects=popular_subjects_ranking,
        top_topics=popular_topics_ranking
    )

@router.get("/traffic", response_model=TrafficSummaryMetrics, dependencies=[admin_protect])
async def fetch_platform_traffic_telemetry(
    interval: ChartInterval = Query(ChartInterval.DAILY),
    days_back: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Extracts underlying system traffic signatures and tracking vectors using download logs
    to track high-volume request timelines.
    """
    timeline_limit = datetime.now(timezone.utc) - timedelta(days=days_back)

    total_hits_stmt = select(func.count(DownloadLog.id)).where(DownloadLog.downloaded_at >= timeline_limit)
    total_hits_ctx = await db.execute(total_hits_stmt)
    total_hits = total_hits_ctx.scalar() or 0

    unique_devices_stmt = select(func.count(func.distinct(DownloadLog.device_fingerprint))).where(
        DownloadLog.downloaded_at >= timeline_limit
    )
    unique_devices_ctx = await db.execute(unique_devices_stmt)
    unique_devices = unique_devices_ctx.scalar() or 0

    traffic_trunc = get_interval_trunc_expression(DownloadLog.downloaded_at, interval)
    timeseries_stmt = (
        select(traffic_trunc.label("period"), func.count(DownloadLog.id).label("value"))
        .where(DownloadLog.downloaded_at >= timeline_limit)
        .group_by("period")
        .order_by("period")
    )
    timeseries_ctx = await db.execute(timeseries_stmt)
    timeseries_points = [
        TimeseriesDataPoint(label=row.period, value=float(row.value or 0))
        for row in timeseries_ctx.all()
    ]

    return TrafficSummaryMetrics(
        total_hits=total_hits,
        unique_devices_count=unique_devices,
        timeseries=timeseries_points
    )
