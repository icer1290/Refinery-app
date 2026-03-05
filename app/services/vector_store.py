"""Vector store operations using pgvector."""

import uuid
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.core.exceptions import DatabaseError
from app.models.orm_models import ArticleEmbedding, NewsArticle

logger = get_logger(__name__)


class VectorStore:
    """PostgreSQL pgvector operations for article embeddings."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    async def store_embedding(
        self,
        session: AsyncSession,
        article_id: uuid.UUID,
        embedding: List[float],
        content_hash: str,
    ) -> ArticleEmbedding:
        """Store embedding for an article.

        Args:
            session: Database session
            article_id: UUID of the article
            embedding: Embedding vector
            content_hash: Hash of the content

        Returns:
            Created ArticleEmbedding instance
        """
        try:
            db_embedding = ArticleEmbedding(
                article_id=article_id,
                embedding=embedding,
                content_hash=content_hash,
            )
            session.add(db_embedding)
            await session.flush()

            logger.debug(
                "Stored embedding",
                article_id=str(article_id),
                content_hash=content_hash[:8],
            )

            return db_embedding

        except Exception as e:
            raise DatabaseError(
                f"Failed to store embedding: {str(e)}",
                {"article_id": str(article_id), "error": str(e)},
            )

    async def find_similar(
        self,
        session: AsyncSession,
        embedding: List[float],
        limit: int = 10,
        exclude_ids: Optional[List[uuid.UUID]] = None,
    ) -> List[tuple[NewsArticle, float]]:
        """Find similar articles by embedding.

        Args:
            session: Database session
            embedding: Query embedding vector
            limit: Maximum number of results
            exclude_ids: Article IDs to exclude

        Returns:
            List of (article, similarity) tuples
        """
        try:
            # Convert embedding to string format for SQL
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            # Build query using cosine similarity
            query = text(
                f"""
                SELECT
                    na.id, na.source_name, na.source_url, na.original_title,
                    na.original_description, na.chinese_title, na.chinese_summary,
                    na.total_score, na.published_at, na.processed_at,
                    ae.embedding <=> :embedding::vector as distance
                FROM news_articles na
                JOIN article_embeddings ae ON na.id = ae.article_id
                WHERE 1 - (ae.embedding <=> :embedding::vector) >= :threshold
                ORDER BY distance
                LIMIT :limit
                """
            )

            params = {
                "embedding": embedding_str,
                "threshold": self.similarity_threshold,
                "limit": limit,
            }

            if exclude_ids:
                # Add exclusion filter
                query = text(
                    query.text.replace(
                        "WHERE",
                        f"WHERE na.id NOT IN ({','.join([f"'{str(id)}'" for id in exclude_ids])}) AND "
                    )
                )

            result = await session.execute(query, params)
            rows = result.fetchall()

            articles = []
            for row in rows:
                article = NewsArticle(
                    id=row[0],
                    source_name=row[1],
                    source_url=row[2],
                    original_title=row[3],
                    original_description=row[4],
                    chinese_title=row[5],
                    chinese_summary=row[6],
                    total_score=row[7],
                    published_at=row[8],
                    processed_at=row[9],
                )
                similarity = 1 - row[10]  # Convert distance to similarity
                articles.append((article, similarity))

            return articles

        except Exception as e:
            raise DatabaseError(
                f"Failed to find similar articles: {str(e)}",
                {"error": str(e)},
            )

    async def check_duplicate_by_hash(
        self,
        session: AsyncSession,
        content_hash: str,
    ) -> Optional[NewsArticle]:
        """Check for duplicate article by content hash.

        Args:
            session: Database session
            content_hash: Hash to check

        Returns:
            Existing article if found, None otherwise
        """
        try:
            stmt = (
                select(NewsArticle)
                .join(ArticleEmbedding)
                .where(ArticleEmbedding.content_hash == content_hash)
                .limit(1)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            raise DatabaseError(
                f"Failed to check duplicate: {str(e)}",
                {"content_hash": content_hash, "error": str(e)},
            )

    async def check_duplicate_by_url(
        self,
        session: AsyncSession,
        url: str,
    ) -> Optional[NewsArticle]:
        """Check for duplicate article by URL.

        Args:
            session: Database session
            url: URL to check

        Returns:
            Existing article if found, None otherwise
        """
        try:
            stmt = select(NewsArticle).where(NewsArticle.source_url == url).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            raise DatabaseError(
                f"Failed to check duplicate URL: {str(e)}",
                {"url": url, "error": str(e)},
            )

    async def delete_embedding(
        self,
        session: AsyncSession,
        article_id: uuid.UUID,
    ) -> bool:
        """Delete embedding for an article.

        Args:
            session: Database session
            article_id: UUID of the article

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(ArticleEmbedding).where(
                ArticleEmbedding.article_id == article_id
            )
            result = await session.execute(stmt)
            embedding = result.scalar_one_or_none()

            if embedding:
                await session.delete(embedding)
                await session.flush()
                return True
            return False

        except Exception as e:
            raise DatabaseError(
                f"Failed to delete embedding: {str(e)}",
                {"article_id": str(article_id), "error": str(e)},
            )


# Singleton instance
vector_store = VectorStore()