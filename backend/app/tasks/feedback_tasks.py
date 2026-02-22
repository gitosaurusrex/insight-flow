"""Celery tasks for AI-powered feedback processing."""

import logging
import re
import uuid

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Lazy-loaded ML models
_sentiment_pipeline = None
_embedding_model = None


def _get_sentiment_pipeline():
    """Lazy-load the sentiment analysis pipeline."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
        )
    return _sentiment_pipeline


def _get_embedding_model():
    """Lazy-load the sentence embedding model."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def clean_text(text: str) -> str:
    """Clean and normalize raw feedback text."""
    text = text.strip()
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"\s+", " ", text)  # Collapse whitespace
    return text


def analyze_sentiment(text: str) -> float:
    """Run sentiment analysis and return score between -1 and 1."""
    pipe = _get_sentiment_pipeline()
    result = pipe(text[:512])[0]
    score = result["score"]
    if result["label"] == "NEGATIVE":
        score = -score
    return round(score, 4)


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """Extract keywords using simple frequency-based approach."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "out", "off", "over",
        "under", "again", "further", "then", "once", "and", "but", "or", "nor",
        "not", "so", "yet", "both", "either", "neither", "each", "every", "all",
        "any", "few", "more", "most", "other", "some", "such", "no", "only",
        "own", "same", "than", "too", "very", "just", "because", "about", "up",
        "it", "its", "i", "me", "my", "we", "our", "you", "your", "he", "him",
        "his", "she", "her", "they", "them", "their", "this", "that", "these",
        "those", "what", "which", "who", "whom", "how", "when", "where", "why",
    }
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in stop_words]
    freq: dict[str, int] = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]


def generate_embedding(text: str) -> list[float]:
    """Generate sentence embedding vector."""
    model = _get_embedding_model()
    embedding = model.encode(text[:512])
    return embedding.tolist()


def categorize_feedback(text: str, sentiment: float, keywords: list[str]) -> str:
    """Categorize feedback based on content analysis."""
    text_lower = text.lower()
    categories = {
        "bug": ["bug", "error", "crash", "broken", "fix", "issue", "fail"],
        "feature_request": ["feature", "request", "add", "want", "need", "wish", "suggest"],
        "praise": ["great", "love", "amazing", "excellent", "awesome", "good", "thank"],
        "complaint": ["bad", "terrible", "worst", "hate", "awful", "poor", "disappoint"],
        "question": ["how", "what", "why", "when", "where", "question", "help"],
    }
    scores: dict[str, int] = {}
    for cat, triggers in categories.items():
        scores[cat] = sum(1 for t in triggers if t in text_lower)

    if sentiment > 0.5:
        scores["praise"] = scores.get("praise", 0) + 2
    elif sentiment < -0.5:
        scores["complaint"] = scores.get("complaint", 0) + 2

    if max(scores.values(), default=0) == 0:
        return "general"
    return max(scores, key=scores.get)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="app.tasks.feedback_tasks.process_feedback",
)
def process_feedback(self, metadata_id: str) -> dict:
    """Process feedback through the AI pipeline.

    Steps: clean text -> sentiment -> keywords -> embedding -> categorize -> update DBs.
    """
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.config import settings
    from app.models.feedback import FeedbackMetadata

    logger.info("Processing feedback %s", metadata_id)

    try:
        # Sync DB connections for Celery
        sync_engine = create_engine(settings.sync_database_url)
        mongo_client = AsyncIOMotorClient(settings.mongo_connection_url)
        mongo_db = mongo_client[settings.MONGO_DB]

        # Fetch raw text from MongoDB
        loop = asyncio.new_event_loop()
        content = loop.run_until_complete(
            mongo_db.feedback_content.find_one({"metadata_id": metadata_id})
        )

        if not content or not content.get("raw_text"):
            logger.error("No content found for feedback %s", metadata_id)
            return {"status": "error", "reason": "no content"}

        raw_text = content["raw_text"]

        # AI pipeline
        cleaned = clean_text(raw_text)
        sentiment = analyze_sentiment(cleaned)
        keywords = extract_keywords(cleaned)
        embedding = generate_embedding(cleaned)
        category = categorize_feedback(cleaned, sentiment, keywords)

        # Update MongoDB
        loop.run_until_complete(
            mongo_db.feedback_content.update_one(
                {"metadata_id": metadata_id},
                {"$set": {
                    "cleaned_text": cleaned,
                    "embedding": embedding,
                    "keywords": keywords,
                    "processed_at": __import__("datetime").datetime.utcnow(),
                }},
            )
        )

        # Update PostgreSQL
        with Session(sync_engine) as session:
            feedback = session.get(FeedbackMetadata, uuid.UUID(metadata_id))
            if feedback:
                feedback.status = "processed"
                feedback.sentiment_score = sentiment
                feedback.category = category
                session.commit()

        # Invalidate analytics cache
        from redis import Redis as SyncRedis
        try:
            redis_client = SyncRedis.from_url(settings.redis_connection_url)
            with Session(sync_engine) as session:
                feedback = session.get(FeedbackMetadata, uuid.UUID(metadata_id))
                if feedback:
                    org_id = str(feedback.org_id)
                    for key in [
                        f"analytics:sentiment:{org_id}",
                        f"analytics:categories:{org_id}",
                        f"analytics:volume:{org_id}",
                    ]:
                        redis_client.delete(key)
            redis_client.close()
        except Exception:
            logger.warning("Failed to invalidate cache", exc_info=True)

        loop.close()
        mongo_client.close()
        sync_engine.dispose()

        logger.info("Successfully processed feedback %s", metadata_id)
        return {"status": "processed", "sentiment": sentiment, "category": category}

    except Exception as exc:
        logger.exception("Error processing feedback %s", metadata_id)
        raise self.retry(exc=exc)
