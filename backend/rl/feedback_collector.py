"""Collect and aggregate developer feedback for RL training."""

import logging

from backend.db.store import ReviewStore
from backend.models import FeedbackCreate, FeedbackRating, FeedbackRecord

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """Stores thumbs up/down and computes helpfulness metrics."""

    def __init__(self, store: ReviewStore | None = None) -> None:
        self.store = store or ReviewStore()

    async def submit(self, data: FeedbackCreate) -> FeedbackRecord:
        record = await self.store.save_feedback(data)
        logger.info(
            "Feedback %s on issue %s (job %s) by %s",
            data.rating.value,
            data.issue_id,
            data.job_id,
            data.user or "anonymous",
        )
        return record

    async def get_helpfulness_score(self) -> float:
        """Return ratio of positive feedback (0.0–1.0)."""
        stats = await self.store.get_feedback_stats()
        total = stats.get("total", 0)
        if total == 0:
            return 0.0
        return stats.get("helpful", 0) / total

    async def should_boost_issue(self, issue_id: int) -> bool:
        """If issue got many 👎, deprioritize similar patterns later (RL-lite)."""
        stats = await self.store.get_issue_feedback_stats(issue_id)
        if stats.get("total", 0) < 3:
            return True
        helpful = stats.get("helpful", 0)
        total = stats["total"]
        return (helpful / total) >= 0.4
