"""Tool implementations for deep search ReAct workflow."""

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.services.embedding import get_embedding_service
from app.services.vector_store import vector_store
from app.services.web_search import get_web_search_service

logger = get_logger(__name__)


class BaseTool:
    """Base class for tools."""

    name: str = "base_tool"
    description: str = "Base tool description"

    async def execute(self, session: AsyncSession, **kwargs) -> str:
        """Execute the tool.

        Args:
            session: Database session
            **kwargs: Tool arguments

        Returns:
            Tool output as string
        """
        raise NotImplementedError


class VectorSearchTool(BaseTool):
    """Tool for searching similar articles in vector store."""

    name = "vector_search"
    description = "Search for similar articles in the local database. Use this to find related news and background information."

    async def execute(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 5,
    ) -> str:
        """Execute vector search.

        Args:
            session: Database session
            query: Search query
            limit: Maximum number of results

        Returns:
            Formatted search results
        """
        try:
            # Generate embedding for query
            embedding_service = get_embedding_service()
            embedding = await embedding_service.embed_text(query)

            # Search for similar articles
            results = await vector_store.find_similar(
                session=session,
                embedding=embedding,
                limit=limit,
            )

            if not results:
                return "No similar articles found in database."

            # Format results
            formatted_results = []
            for article, similarity in results:
                formatted_results.append({
                    "title": article.chinese_title or article.original_title,
                    "summary": article.chinese_summary or article.original_description,
                    "source": article.source_name,
                    "published_at": str(article.published_at) if article.published_at else "Unknown",
                    "similarity": round(similarity, 3),
                    "url": article.source_url,
                })

            logger.info(
                "Vector search completed",
                query=query[:50],
                results_count=len(results),
            )

            return json.dumps(formatted_results, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error("Vector search failed", error=str(e), query=query[:50])
            return f"Vector search failed: {str(e)}"


class WebSearchTool(BaseTool):
    """Tool for searching the web for information."""

    name = "web_search"
    description = "Search the web for information about companies, technologies, and events. Use this to find external background information."

    async def execute(
        self,
        session: AsyncSession,
        query: str,
    ) -> str:
        """Execute web search.

        Args:
            session: Database session (unused but required for interface)
            query: Search query

        Returns:
            Formatted search results
        """
        try:
            web_search = get_web_search_service()
            results = await web_search.search(query, max_results=5)

            if not results:
                return "No results found on the web."

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.title,
                    "snippet": result.snippet,
                    "url": result.url,
                })

            logger.info(
                "Web search completed",
                query=query[:50],
                results_count=len(results),
            )

            return json.dumps(formatted_results, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error("Web search failed", error=str(e), query=query[:50])
            return f"Web search failed: {str(e)}"


# Tool registry
TOOLS: dict[str, BaseTool] = {
    "vector_search": VectorSearchTool(),
    "web_search": WebSearchTool(),
}


def get_tool(tool_name: str) -> BaseTool | None:
    """Get a tool by name.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool instance or None if not found
    """
    return TOOLS.get(tool_name)


async def execute_tool(
    session: AsyncSession,
    tool_name: str,
    tool_input: dict[str, Any],
) -> str:
    """Execute a tool by name.

    Args:
        session: Database session
        tool_name: Name of the tool
        tool_input: Tool input arguments

    Returns:
        Tool output as string
    """
    tool = get_tool(tool_name)
    if not tool:
        return f"Unknown tool: {tool_name}"

    try:
        return await tool.execute(session, **tool_input)
    except Exception as e:
        logger.error("Tool execution failed", tool=tool_name, error=str(e))
        return f"Tool execution failed: {str(e)}"