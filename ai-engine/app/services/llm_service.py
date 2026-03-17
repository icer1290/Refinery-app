"""LLM service for text generation and scoring."""

import json
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core import get_logger
from app.core.exceptions import LLMError
from app.models.schemas import ReflectionResult, ScoringResult, TranslationResult

logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    """Service for LLM operations using LangChain and OpenAI-compatible APIs."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model or settings.openai_chat_model
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url

        if not self.api_key:
            raise LLMError("API key not configured")

        # Build ChatOpenAI with optional custom base_url
        llm_kwargs = {
            "model": self.model,
            "api_key": self.api_key,
            "temperature": 0.3,  # Lower temperature for more consistent outputs
            "extra_body": {"enable_thinking": False},
        }

        # Add base_url if provided (for DashScope, etc.)
        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        self.llm = ChatOpenAI(**llm_kwargs)

        logger.info(
            "LLM service initialized",
            model=self.model,
            base_url=self.base_url or "default",
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def score_article(
        self,
        title: str,
        description: str,
        content: Optional[str] = None,
    ) -> ScoringResult:
        """Score an article on multiple dimensions.

        Args:
            title: Article title
            description: Article description
            content: Full article content (optional)

        Returns:
            ScoringResult with scores and reasoning
        """
        prompt = self._build_scoring_prompt(title, description, content)

        try:
            response = await self.llm.ainvoke(prompt)
            result = self._parse_scoring_response(response.content)

            logger.debug(
                "Scored article",
                title=title[:50],
                total_score=result.total_score,
            )

            return result

        except Exception as e:
            raise LLMError(
                f"Failed to score article: {str(e)}",
                {"title": title, "error": str(e)},
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def translate_and_summarize(
        self,
        title: str,
        content: str,
        entities_to_preserve: Optional[list[str]] = None,
    ) -> TranslationResult:
        """Translate and summarize article to Chinese.

        Args:
            title: Original article title
            content: Full article content
            entities_to_preserve: List of entities to keep in original language

        Returns:
            TranslationResult with Chinese title and summary
        """
        prompt = self._build_translation_prompt(title, content, entities_to_preserve)

        try:
            response = await self.llm.ainvoke(prompt)
            result = self._parse_translation_response(response.content)

            logger.info(
                "Translated article",
                original_title=title[:50],
                chinese_title=result.chinese_title[:50],
            )

            return result

        except Exception as e:
            raise LLMError(
                f"Failed to translate article: {str(e)}",
                {"title": title, "error": str(e)},
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def reflect(
        self,
        chinese_title: str,
        chinese_summary: str,
        original_title: str,
        original_content: str,
    ) -> ReflectionResult:
        """Reflect on translation quality.

        Args:
            chinese_title: Translated Chinese title
            chinese_summary: Translated Chinese summary
            original_title: Original article title
            original_content: Original article content

        Returns:
            ReflectionResult with pass/fail and feedback
        """
        prompt = self._build_reflection_prompt(
            chinese_title,
            chinese_summary,
            original_title,
            original_content,
        )

        try:
            response = await self.llm.ainvoke(prompt)
            result = self._parse_reflection_response(response.content)

            logger.debug(
                "Reflected on translation",
                passed=result.passed,
                issues_count=len(result.issues),
            )

            return result

        except Exception as e:
            raise LLMError(
                f"Failed to reflect on translation: {str(e)}",
                {"chinese_title": chinese_title, "error": str(e)},
            )

    def _build_scoring_prompt(
        self, title: str, description: str, content: Optional[str]
    ) -> str:
        """Build prompt for article scoring."""
        content_section = f"\n\nContent:\n{content[:2000]}" if content else ""

        return f"""你是一位科技新闻编辑专家。请从以下三个维度对文章进行评分(0-10分):

1. 行业影响力 (industry_impact_score): 对科技行业的影响力
   - 是否涉及重大技术突破或产品发布
   - 是否影响行业格局或市场趋势
   - 对开发者和企业的影响程度

2. 关键节点 (milestone_score): 事件的里程碑意义
   - 是否代表技术发展的重要节点
   - 是否开创先例或改变现状
   - 历史意义和长期价值

3. 引人关注 (attention_score): 新闻价值
   - 受众广泛程度
   - 话题热度和传播潜力
   - 时效性和独特性

文章标题: {title}
文章描述: {description}{content_section}

请以JSON格式返回评分结果:
{{
    "industry_impact_score": <分数>,
    "milestone_score": <分数>,
    "attention_score": <分数>,
    "reasoning": "<评分理由简述>"
}}

只返回JSON，不要添加其他内容。"""

    def _build_translation_prompt(
        self,
        title: str,
        content: str,
        entities_to_preserve: Optional[list[str]] = None,
    ) -> str:
        """Build prompt for translation and summarization."""
        entities_section = ""
        if entities_to_preserve:
            entities_section = f"\n\n**实体保留要求**：以下专有名词请保留原文（人名/公司名/产品名）：{', '.join(entities_to_preserve)}"

        return f"""## Role
你是一位冷静、犀利且极具洞察力的科技新闻资深编辑，擅长从复杂的工程文档和战略报告中榨取核心价值。

## Task
请基于提供的文章全文，撰写一段极简、高信息密度的中文专业简报。

## Output Structure (不显示“**标题**” ”**第一段 (核心内容)**” 等；标题要包含[领域]标签)
**标题**：[领域] （将原文标题翻译为中文，调整语序，保持与原文的逻辑一致）
1. **第一段 (核心内容)**：格式为 `动作 + 关键结果`。紧随其后是一个句号，并用一句话陈述最核心的行业变量。
2. **第二段 (关键事实)**：以几个要点（2-3 个）列出核心数据、技术参数或战略动作。
3. **第三段 (专家点评)**：以"主编洞察"的视角，用 3-5 句话点破其对行业格局、竞品逻辑或未来演进的深层影响。

## Style & Rules
- **禁止标签**：严禁在输出中出现"标题"、"钩子"、"核心事实"、"深度洞察"等任何指示性标签。
- **去除废话**：严禁使用"据悉"、"令人震惊"、"本文介绍了"、"...具有里程碑意义"等公关词汇或AI腔。
- **数据驱动**：原文中的数字、百分比、融资金额、技术参数必须精准保留在事实要点中。
- **冷静权威**：语气应像给顶级决策者看的简报，保持客观、克制且具有穿透力。
- **篇幅限制**：全文严格控制在 300 字以内。
{entities_section}
## Example
[创业公司] Cluely CEO承认虚报年收入
Cluely创始人兼CEO Roy Lee在X平台公开承认，去年向TechCrunch披露的700万美元年经常性收入（ARR）为虚假数据。此举暴露其早期依赖炒作驱动增长的模式已难以为继，行业对初创企业可信度的审查正加速收紧。

· 2025年夏季，Cluely宣称拥有700万美元ARR，后被证实为虚构；实际营收数据来自其Stripe账户，未公开具体金额。
· 公司于2025年6月完成1500万美元Series A融资，由Andreessen Horowitz领投，此前已获530万美元种子轮融资。
· 该公司原定位为“面试作弊工具”，现转型为AI会议笔记产品，但其营销策略仍以病毒式争议为核心。

主编洞察：虚报数据并非孤立事件，而是典型“现象级初创”在缺乏可持续商业模式时的生存策略。当舆论热度退潮，真实财务表现成为唯一检验标准。该事件将倒逼风投机构强化尽调维度，从“传播力”转向“现金流健康度”。未来，所有以情绪驱动增长的AI应用都将面临更严苛的合规与透明度压力。

---

**文章标题**: {title}

**文章内容**:
{content}

请以JSON格式返回:
{{
    "chinese_title": "<标题，即[领域] + 标题>",
    "chinese_summary": "<完整简报内容，包含三段>",
    "entities_preserved": ["<保留原文的实体列表>"]
}}

只返回JSON，不要添加其他内容。"""

    def _build_reflection_prompt(
        self,
        chinese_title: str,
        chinese_summary: str,
        original_title: str,
        original_content: str,
    ) -> str:
        """Build prompt for reflection check."""
        content_preview = original_content[:500] if original_content else "（无内容）"

        return f"""请检查以下翻译是否符合要求:

原文标题: {original_title}
原文内容片段: {content_preview}

中文标题: {chinese_title}
中文摘要: {chinese_summary}

检查项目(只检查以下两点格式，不检查具体信息，且大致符合格式要求即可):
1. 格式合规: 中文标题开头应包含[领域]标签
2. 摘要包含三部分结构（核心内容、关键事实、主编洞察），不评判内容，格式与以下 example 结构相同即可：
    ## Example
    [创业公司] Cluely CEO承认虚报年收入
    Cluely创始人兼CEO Roy Lee在X平台公开承认，去年向TechCrunch披露的700万美元年经常性收入（ARR）为虚假数据。此举暴露其早期依赖炒作驱动增长的模式已难以为继，行业对初创企业可信度的审查正加速收紧。

    · 2025年夏季，Cluely宣称拥有700万美元ARR，后被证实为虚构；实际营收数据来自其Stripe账户，未公开具体金额。
    · 公司于2025年6月完成1500万美元Series A融资，由Andreessen Horowitz领投，此前已获530万美元种子轮融资。
    · 该公司原定位为“面试作弊工具”，现转型为AI会议笔记产品，但其营销策略仍以病毒式争议为核心。

    主编洞察：虚报数据并非孤立事件，而是典型“现象级初创”在缺乏可持续商业模式时的生存策略。当舆论热度退潮，真实财务表现成为唯一检验标准。该事件将倒逼风投机构强化尽调维度，从“传播力”转向“现金流健康度”。未来，所有以情绪驱动增长的AI应用都将面临更严苛的合规与透明度压力。

3. 实体保留: 重要人名、公司名、产品名是否正确处理

请以JSON格式返回检查结果:
{{
    "passed": <true或false>,
    "issues": ["<问题列表>"],
    "feedback": "<改进建议，如果没有问题则为null>"
}}

只返回JSON，不要添加其他内容。"""

    def _parse_scoring_response(self, response: str) -> ScoringResult:
        """Parse LLM response for scoring."""
        try:
            # Extract JSON from response
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            industry_impact = float(data["industry_impact_score"])
            milestone = float(data["milestone_score"])
            attention = float(data["attention_score"])

            # Calculate weighted total score
            total = (
                0.4 * industry_impact + 0.35 * milestone + 0.25 * attention
            )

            return ScoringResult(
                industry_impact_score=industry_impact,
                milestone_score=milestone,
                attention_score=attention,
                total_score=total,
                reasoning=data.get("reasoning"),
            )
        except Exception as e:
            raise LLMError(f"Failed to parse scoring response: {str(e)}")

    def _parse_translation_response(self, response: str) -> TranslationResult:
        """Parse LLM response for translation."""
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            return TranslationResult(
                chinese_title=data["chinese_title"],
                chinese_summary=data["chinese_summary"],
                entities_preserved=data.get("entities_preserved", []),
            )
        except Exception as e:
            raise LLMError(f"Failed to parse translation response: {str(e)}")

    def _parse_reflection_response(self, response: str) -> ReflectionResult:
        """Parse LLM response for reflection."""
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            return ReflectionResult(
                passed=data["passed"],
                feedback=data.get("feedback"),
                issues=data.get("issues", []),
            )
        except Exception as e:
            raise LLMError(f"Failed to parse reflection response: {str(e)}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain markdown code blocks."""
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        # Try to find JSON object directly
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return text[start:end]
        return text


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service