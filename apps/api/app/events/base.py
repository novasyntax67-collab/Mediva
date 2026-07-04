"""
Domain Event base definitions.

Re-exports from the shared backend-core events package so that
API-layer code can import from `app.events.base` without needing
direct path manipulation to `packages/backend-core/events/`.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from events.base import DomainEvent

__all__ = ["DomainEvent"]
