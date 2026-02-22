"""Scheduled aggregation tasks."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select, func, cast, Date
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.feedback import FeedbackMetadata
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.aggregation_tasks.daily_aggregation")
def daily_aggregation() -> dict:
    """Run daily aggregation of feedback data.

    Computes summary statistics for the previous day and logs them.
    """
    engine = create_engine(settings.sync_database_url)
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

    try:
        with Session(engine) as session:
            result = session.execute(
                select(
                    func.count(FeedbackMetadata.id).label("total"),
                    func.avg(FeedbackMetadata.sentiment_score).label("avg_sentiment"),
                ).where(
                    cast(FeedbackMetadata.created_at, Date) == yesterday,
                    FeedbackMetadata.status == "processed",
                )
            )
            row = result.one()

            summary = {
                "date": str(yesterday),
                "total_feedback": row.total or 0,
                "avg_sentiment": round(float(row.avg_sentiment or 0), 4),
            }

            logger.info("Daily aggregation for %s: %s", yesterday, summary)
            return summary

    except Exception:
        logger.exception("Daily aggregation failed")
        raise
    finally:
        engine.dispose()
