from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

try:
    from langfuse import get_client, observe, propagate_attributes

    class _LangfuseContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(
            self,
            *,
            metadata: dict[str, Any] | None = None,
            usage_details: dict[str, int] | None = None,
            **kwargs: Any,
        ) -> None:
            client = get_client()
            span_metadata = dict(metadata or {})
            if usage_details:
                span_metadata["usage_details"] = usage_details
            if span_metadata:
                client.update_current_span(metadata=span_metadata)

    langfuse_context = _LangfuseContext()

    @contextmanager
    def propagate_trace_attributes(**kwargs: Any) -> Iterator[None]:
        with propagate_attributes(**kwargs):
            yield

except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()

    @contextmanager
    def propagate_trace_attributes(**kwargs: Any) -> Iterator[None]:
        yield


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def flush_traces() -> None:
    if not tracing_enabled():
        return
    try:
        get_client().flush()
    except Exception:  # pragma: no cover
        return
