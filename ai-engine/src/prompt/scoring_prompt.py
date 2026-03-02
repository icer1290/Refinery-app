"""
Scoring prompt templates
"""

with open('src/prompt/scoring_prompt.md', 'r', encoding='utf-8') as f:
    SCORING_PROMPT = f.read()

with open('src/prompt/summary_prompt.md', 'r', encoding='utf-8') as f:
    SUMMARY_PROMPT = f.read()

with open('src/prompt/simple_summary_prompt.md', 'r', encoding='utf-8') as f:
    SIMPLE_SUMMARY_PROMPT = f.read()
