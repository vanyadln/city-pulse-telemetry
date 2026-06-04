import os
import requests
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

HF_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

def get_sentiment_score(text: str, retries: int = 3) -> Optional[float]:
    """
    Returns a sentiment score in range [-1.0, 1.0].
    -1.0 = very negative, 0.0 = neutral, 1.0 = very positive.
    Uses HuggingFace free Inference API (no GPU needed).
    """
    token = os.getenv("HF_API_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Truncate text to 512 chars — model limit
    text = text[:512].strip()
    if not text:
        return 0.0

    for attempt in range(retries):
        try:
            resp = requests.post(
                HF_API_URL,
                headers=headers,
                json={"inputs": text},
                timeout=10,
            )
            if resp.status_code == 503:
                # Model is loading — wait and retry
                wait = resp.json().get("estimated_time", 20)
                logger.info(f"Model loading, waiting {wait:.0f}s...")
                time.sleep(min(wait, 30))
                continue

            resp.raise_for_status()
            results = resp.json()

            # Response: [[{label, score}, ...]]
            if not results or not results[0]:
                return 0.0

            scores = {item["label"]: item["score"] for item in results[0]}
            # Labels: positive, neutral, negative
            pos = scores.get("positive", 0)
            neg = scores.get("negative", 0)
            # Map to [-1, 1]
            return round(pos - neg, 4)

        except requests.exceptions.Timeout:
            logger.warning(f"HF API timeout (attempt {attempt+1})")
        except Exception as e:
            logger.error(f"Sentiment error: {e}")
            break

    return 0.0


def score_to_label(score: float) -> str:
    if score > 0.3:
        return "positive"
    elif score < -0.3:
        return "negative"
    return "neutral"


def score_to_color_intensity(score: float) -> float:
    """Returns 0.0–1.0 for heatmap intensity."""
    return round((score + 1) / 2, 4)