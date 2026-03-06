"""Tests for LLM service."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.llm_service import LLMService
from app.models.schemas import ScoringResult, TranslationResult, ReflectionResult


@pytest.fixture
def mock_settings():
    with patch("app.services.llm_service.settings") as mock:
        mock.openai_chat_model = "gpt-4o-mini"
        mock.openai_api_key = "test-key"
        yield mock


@pytest.mark.asyncio
async def test_extract_json():
    """Test JSON extraction from LLM response."""
    service = LLMService(api_key="test-key")

    # Plain JSON
    json_text = '{"key": "value"}'
    extracted = service._extract_json(json_text)
    assert extracted == '{"key": "value"}'

    # JSON in code block
    code_block = '```json\n{"key": "value"}\n```'
    extracted = service._extract_json(code_block)
    assert extracted == '{"key": "value"}'

    # JSON with surrounding text
    mixed_text = 'Some text {"key": "value"} more text'
    extracted = service._extract_json(mixed_text)
    assert extracted == '{"key": "value"}'


@pytest.mark.asyncio
async def test_parse_scoring_response(mock_settings):
    """Test parsing scoring response."""
    service = LLMService(api_key="test-key")

    response = '{"industry_impact_score": 8, "milestone_score": 7, "attention_score": 9, "reasoning": "Test"}'
    result = service._parse_scoring_response(response)

    assert isinstance(result, ScoringResult)
    assert result.industry_impact_score == 8
    assert result.milestone_score == 7
    assert result.attention_score == 9
    # Total = 0.4 * 8 + 0.35 * 7 + 0.25 * 9 = 3.2 + 2.45 + 2.25 = 7.9
    assert result.total_score == pytest.approx(7.9, rel=0.01)


@pytest.mark.asyncio
async def test_parse_translation_response(mock_settings):
    """Test parsing translation response."""
    service = LLMService(api_key="test-key")

    response = '{"chinese_title": "中文标题", "chinese_summary": "中文摘要", "entities_preserved": ["OpenAI"]}'
    result = service._parse_translation_response(response)

    assert isinstance(result, TranslationResult)
    assert result.chinese_title == "中文标题"
    assert result.chinese_summary == "中文摘要"
    assert "OpenAI" in result.entities_preserved


@pytest.mark.asyncio
async def test_parse_reflection_response(mock_settings):
    """Test parsing reflection response."""
    service = LLMService(api_key="test-key")

    response = '{"passed": true, "issues": [], "feedback": null}'
    result = service._parse_reflection_response(response)

    assert isinstance(result, ReflectionResult)
    assert result.passed is True
    assert len(result.issues) == 0

    # Failed reflection
    response = '{"passed": false, "issues": ["问题1"], "feedback": "改进建议"}'
    result = service._parse_reflection_response(response)

    assert result.passed is False
    assert len(result.issues) == 1
    assert result.feedback == "改进建议"