"""
Per-request context shared between middleware and services.

The audit middleware stores the caller's network details here so services can write
activity entries without every function taking a ``Request`` argument. A service that
records a domain event marks the request as recorded, and the middleware then skips its
generic "request" entry so the activity log carries one meaningful row per action.
"""
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RequestContext:
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    activity_recorded: bool = False
    extra: dict = field(default_factory=dict)


_current: ContextVar[Optional[RequestContext]] = ContextVar("educore_request_context", default=None)


def set_request_context(ctx: RequestContext):
    return _current.set(ctx)


def reset_request_context(token) -> None:
    _current.reset(token)


def get_request_context() -> Optional[RequestContext]:
    return _current.get()
