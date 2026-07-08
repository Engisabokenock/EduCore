import hashlib
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, desc
from app.core.database import get_db
from app.core.cache import CacheManager
from app.models.resource import AcademicResource
from app.schemas.search import SearchFilterPayload, PaginatedSearchResults, SearchSortOrder
from app.schemas.resource import ResourceOut

router = APIRouter(prefix="/search", tags=["High-Performance Search Optimization Pipeline Engine"])

# High-frequency read path: cache identical searches for 10 minutes to offload the database.
SEARCH_CACHE_TTL_SECONDS = 600

@router.post("", response_model=PaginatedSearchResults, status_code=status.HTTP_200_OK)
async def execute_advanced_curriculum_search(
    payload: SearchFilterPayload,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a high-performance database search combining multiple parameters.

    Supports pagination, advanced sorting algorithms, and text filtering across titles and descriptions.
    """
    # Cache-Aside: serve identical searches directly from Redis before hitting the database.
    # Key is derived from a stable hash of the request body (POST payloads are not in the query string).
    payload_fingerprint = hashlib.md5(
        json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()
    cache_key = f"cache:search:{payload_fingerprint}"

    cached_response = await CacheManager.get(cache_key)
    if cached_response is not None:
        return cached_response

    now = datetime.now(timezone.utc)

    # Strict compliance lifecycle filtering criteria. Excludes all unreleased or archived assets.
    base_conditions = [
        AcademicResource.is_archived == False,
        or_(
            AcademicResource.is_published == True,
            and_(
                AcademicResource.scheduled_publish_at != None,
                AcademicResource.scheduled_publish_at <= now
            )
        )
    ]

    # Dynamically inject filtration elements depending on user criteria payload mapping
    if payload.grade_id:
        base_conditions.append(AcademicResource.grade_id == payload.grade_id)

    if payload.subject_id:
        base_conditions.append(AcademicResource.subject_id == payload.subject_id)

    if payload.topic_id:
        base_conditions.append(AcademicResource.topic_id == payload.topic_id)

    if payload.is_premium is not None:
        base_conditions.append(AcademicResource.is_premium == payload.is_premium)

    if payload.type_variant:
        base_conditions.append(AcademicResource.type_variant == payload.type_variant)

    if payload.year:
        base_conditions.append(AcademicResource.year == payload.year)

    if payload.term:
        base_conditions.append(AcademicResource.term == payload.term)

    if payload.keyword:
        sanitized_keyword = f"%{payload.keyword.strip().lower()}%"
        base_conditions.append(
            or_(
                func.lower(AcademicResource.title).like(sanitized_keyword),
                func.lower(AcademicResource.description).like(sanitized_keyword)
            )
        )

    # 1. Total Count Aggregation Pipeline Execution Block for exact paginated bounds computations
    count_statement = select(func.count(AcademicResource.id)).where(and_(*base_conditions))
    count_execution_context = await db.execute(count_statement)
    total_matched_records: int = count_execution_context.scalar() or 0

    # 2. Base Resource Query Segment Thread Allocation Construction
    selection_statement = select(AcademicResource).where(and_(*base_conditions))

    # 3. Dynamic Structural Sorting Algorithm Routing Logic Matrix Mapping Execution
    if payload.sort_by == SearchSortOrder.NEWEST:
        selection_statement = selection_statement.order_by(desc(AcademicResource.created_at))

    elif payload.sort_by == SearchSortOrder.MOST_DOWNLOADED:
        selection_statement = selection_statement.order_by(desc(AcademicResource.downloads_count))

    elif payload.sort_by == SearchSortOrder.POPULARITY:
        # Algorithmic popularity score: combines analytical views matrix scale with heavily-weighted downloads counters
        calculated_popularity_score = AcademicResource.views_count + (AcademicResource.downloads_count * 4)
        selection_statement = selection_statement.order_by(desc(calculated_popularity_score))

    # 4. Strict Offset Boundary Allocation Pagination Execution Controls Calculations
    calculated_offset_index = (payload.page - 1) * payload.page_size
    selection_statement = selection_statement.offset(calculated_offset_index).limit(payload.page_size)

    # Execute fetch transaction logs pipeline against the underlying pool
    records_execution_context = await db.execute(selection_statement)
    retrieved_resource_records = records_execution_context.scalars().all()

    # 5. Metadata Structural Summary Output Payload Calculations Construction
    total_computed_pages = max((total_matched_records + payload.page_size - 1) // payload.page_size, 1)

    pagination_metadata_response = {
        "total_records": total_matched_records,
        "total_pages": total_computed_pages,
        "current_page": payload.page,
        "page_size": payload.page_size,
        "has_next": payload.page < total_computed_pages,
        "has_previous": payload.page > 1
    }

    # Serialize ORM rows to plain dicts so they can be stored/retrieved as JSON in Redis.
    serialized_results = [
        ResourceOut.model_validate(record).model_dump(mode="json")
        for record in retrieved_resource_records
    ]
    cacheable_response = {
        "metadata": pagination_metadata_response,
        "results": serialized_results
    }

    # Asynchronously populate the cache for subsequent hits (cache-aside write-through).
    await CacheManager.set(cache_key, cacheable_response, expire_seconds=SEARCH_CACHE_TTL_SECONDS)

    return cacheable_response
