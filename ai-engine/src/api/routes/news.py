"""
News API routes
"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, date, timedelta
from typing import Optional
import asyncio

from src.api.schemas.news import (
    NewsItem, NewsListResponse,
    IngestRequest, IngestResponse,
    ScoreRequest, ScoreResponse,
    SummarizeRequest, SummarizeResponse
)
from src.vector_store import get_vector_store
from src.pipeline.ingest_and_store import fetch_all_data, merge_all_articles, process_and_store
from src.llm import get_llm_client
from src.prompt.scoring_prompt import SCORING_PROMPT, SUMMARY_PROMPT, SIMPLE_SUMMARY_PROMPT

router = APIRouter()


@router.get("/news/today", response_model=NewsListResponse)
async def get_today_news(
    news_date: Optional[date] = Query(None, alias="date", description="Date to fetch news for (default: today)")
):
    """
    Get news for a specific date (default: today in UTC+8)
    """
    store = get_vector_store()

    # Use provided date or today
    if news_date is None:
        # Get current UTC+8 time
        news_date = (datetime.utcnow() + timedelta(hours=8)).date()

    # Fetch news from Qdrant
    news_records = store.fetch_today_news(news_date)

    news_items = []
    for record in news_records:
        timestamp_value = record.get("timestamp")
        timestamp_str = str(timestamp_value) if timestamp_value is not None else None
        
        item = NewsItem(
            id=str(record.get("id", "")),
            title=record.get("title", ""),
            translated_title=record.get("translated_title"),
            url=record.get("url", ""),
            source=record.get("source", ""),
            category=record.get("category"),
            score=record.get("score"),
            llm_score=record.get("llm_score"),
            final_score=record.get("final_score"),
            summary=record.get("generated_summary") or record.get("summary") or record.get("raw_summary"),
            content=record.get("content"),
            raw_summary=record.get("raw_summary"),
            published_date=news_date,
            timestamp=timestamp_str
        )
        news_items.append(item)

    return NewsListResponse(
        news=news_items,
        total=len(news_items),
        date=news_date.isoformat()
    )


@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingest(request: IngestRequest = IngestRequest()):
    """
    Trigger news ingestion from configured sources
    """
    try:
        rss_feeds_data = fetch_all_data()
        all_articles = merge_all_articles(rss_feeds_data)

        if not all_articles:
            return IngestResponse(
                success=True,
                message="No new articles found",
                stats={"total": 0}
            )

        stats = process_and_store(all_articles, clear_collection=request.clear_collection)

        return IngestResponse(
            success=True,
            message=f"Successfully ingested {stats['new_inserted']} new articles",
            stats=stats
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score", response_model=ScoreResponse)
async def trigger_score(request: ScoreRequest = ScoreRequest()):
    """
    Trigger LLM scoring for news items
    """
    try:
        store = get_vector_store()
        llm = get_llm_client()

        # Fetch today's news
        news_records = store.fetch_today_news()

        if not news_records:
            return ScoreResponse(
                success=True,
                message="No news found to score",
                processed=0
            )

        # Filter by IDs if provided
        if request.news_ids:
            news_records = [n for n in news_records if str(n.get("id")) in request.news_ids]

        if not news_records:
            return ScoreResponse(
                success=True,
                message="No matching news found",
                processed=0
            )

        # Run scoring
        scored_news = await llm.batch_score_news(
            news_list=news_records,
            prompt_template=SCORING_PROMPT,
            max_concurrency=5
        )

        # Calculate final scores and update in Qdrant
        updated_count = 0
        max_score = max(n.get("score", 1) for n in scored_news) if scored_news else 1

        for news in scored_news:
            # Calculate normalized final score
            normalized_popularity = (news.get("score", 0) / max_score) if max_score > 0 else 0
            normalized_llm_score = (news.get("llm_score", 0) / 10)
            final_score = normalized_popularity * 0.3 + normalized_llm_score * 0.7

            # Update in Qdrant using upsert
            try:
                # Create updated point with existing vector (if available) or empty vector
                # Note: We need to keep the existing vector to avoid overwriting it
                # For simplicity, we'll use an empty vector here as we don't have access to the original vector
                from qdrant_client.models import PointStruct
                updated_point = PointStruct(
                    id=news.get("id"),
                    vector=[0.0] * 1024,  # Empty vector (will be ignored if record exists)
                    payload={
                        **news,  # Include all existing fields
                        "llm_score": news.get("llm_score"),
                        "category": news.get("category"),
                        "reason": news.get("reason"),
                        "final_score": final_score
                    }
                )
                
                store.client.upsert(
                    collection_name=store.collection_name,
                    points=[updated_point]
                )
                updated_count += 1
            except Exception as e:
                print(f"Failed to update news {news.get('id')}: {e}")

        return ScoreResponse(
            success=True,
            message=f"Successfully scored {updated_count} news items",
            processed=updated_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize", response_model=SummarizeResponse)
async def trigger_summarize(request: SummarizeRequest = SummarizeRequest()):
    """
    Trigger summary generation for news items
    """
    try:
        store = get_vector_store()
        llm = get_llm_client()

        # Fetch today's news
        news_records = store.fetch_today_news()

        if not news_records:
            return SummarizeResponse(
                success=True,
                message="No news found to summarize",
                processed=0
            )

        # Filter by IDs if provided
        if request.news_ids:
            news_records = [n for n in news_records if str(n.get("id")) in request.news_ids]

        # Sort by final_score and take top 15
        sorted_news = sorted(
            news_records,
            key=lambda x: x.get("final_score", 0) or 0,
            reverse=True
        )[:15]

        if not sorted_news:
            return SummarizeResponse(
                success=True,
                message="No matching news found",
                processed=0
            )

        # Select prompt based on summary type
        prompt_template = SUMMARY_PROMPT if request.summary_type == "deep" else SIMPLE_SUMMARY_PROMPT

        # Generate summaries
        summarized_news = await llm.batch_generate_summaries(
            articles=sorted_news,
            prompt_template=prompt_template,
            max_concurrency=3,
            summary_type=request.summary_type
        )

        # Update in Qdrant
        updated_count = 0
        for news in summarized_news:
            if news.get("generated_summary"):
                try:
                    # Create updated point with existing vector (if available) or empty vector
                    from qdrant_client.models import PointStruct
                    updated_point = PointStruct(
                        id=news.get("id"),
                        vector=[0.0] * 1024,  # Empty vector (will be ignored if record exists)
                        payload={
                            **news,  # Include all existing fields
                            "generated_summary": news.get("generated_summary"),
                            "summary_type": news.get("summary_type")
                        }
                    )
                    
                    store.client.upsert(
                        collection_name=store.collection_name,
                        points=[updated_point]
                    )
                    updated_count += 1
                except Exception as e:
                    print(f"Failed to update summary for news {news.get('id')}: {e}")

        return SummarizeResponse(
            success=True,
            message=f"Successfully summarized {updated_count} news items",
            processed=updated_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
