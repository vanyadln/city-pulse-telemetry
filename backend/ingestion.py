import os
import logging
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import AsyncGenerator
import praw

from cities import CITIES, City
from sentiment import get_sentiment_score, score_to_label, score_to_color_intensity

logger = logging.getLogger(__name__)


def get_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "CityPulse/1.0"),
        read_only=True,
    )


def build_event(city: City, source: str, title: str, body: str, url: str) -> dict:
    text = f"{title}. {body}"[:600]
    score = get_sentiment_score(text)
    return {
        "city": city.name,
        "lat": city.lat,
        "lng": city.lng,
        "source": source,
        "title": title[:120],
        "snippet": body[:200],
        "url": url,
        "sentiment_score": score,
        "sentiment_label": score_to_label(score),
        "intensity": score_to_color_intensity(score),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_reddit_events(city: City, limit: int = 5) -> list[dict]:
    """Fetch hot posts from city subreddits and score them."""
    events = []
    try:
        reddit = get_reddit_client()
        for subreddit_name in city.subreddits[:2]:  # max 2 subreddits per city
            try:
                subreddit = reddit.subreddit(subreddit_name)
                for post in subreddit.hot(limit=limit):
                    if post.stickied:
                        continue
                    event = build_event(
                        city=city,
                        source="reddit",
                        title=post.title,
                        body=post.selftext or "",
                        url=f"https://reddit.com{post.permalink}",
                    )
                    events.append(event)
                    await asyncio.sleep(0.3)  # rate limit courtesy
            except Exception as e:
                logger.warning(f"Reddit subreddit {subreddit_name} error: {e}")
    except Exception as e:
        logger.error(f"Reddit client error for {city.name}: {e}")
    return events


async def fetch_news_events(session: aiohttp.ClientSession, city: City, limit: int = 3) -> list[dict]:
    """Fetch top headlines from NewsAPI for a city."""
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key:
        logger.warning("No NEWS_API_KEY set, skipping news fetch")
        return []

    events = []
    params = {
        "q": city.news_query,
        "sortBy": "publishedAt",
        "pageSize": limit,
        "language": "en",
        "apiKey": api_key,
    }
    try:
        async with session.get(
            "https://newsapi.org/v2/everything",
            params=params,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            data = await resp.json()
            articles = data.get("articles", [])
            for article in articles:
                event = build_event(
                    city=city,
                    source="news",
                    title=article.get("title", ""),
                    body=article.get("description", "") or "",
                    url=article.get("url", ""),
                )
                events.append(event)
    except Exception as e:
        logger.warning(f"NewsAPI error for {city.name}: {e}")
    return events


async def run_ingestion_cycle() -> list[dict]:
    """
    Full ingestion cycle: polls all cities for Reddit + News,
    scores sentiment, returns list of events.
    Called every POLL_INTERVAL seconds by the pipeline loop.
    """
    all_events = []
    async with aiohttp.ClientSession() as session:
        for city in CITIES:
            logger.info(f"Ingesting city: {city.name}")
            reddit_events = await fetch_reddit_events(city, limit=3)
            news_events = await fetch_news_events(session, city, limit=2)
            all_events.extend(reddit_events)
            all_events.extend(news_events)
            await asyncio.sleep(1)  # be gentle to APIs between cities

    logger.info(f"Ingestion cycle complete: {len(all_events)} events")
    return all_events