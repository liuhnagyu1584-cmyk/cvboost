import os
import time
import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI
from agent.config import (
    MODEL_NAME,
    MODEL_BASE_URL,
    MODEL_API_KEY,
    LLM_TIMEOUT_SECONDS,
    LLM_MAX_RETRIES,
    LLM_RETRY_BACKOFF_BASE,
    THINKING_ENABLED,
)
from agent.system_prompt import get_system_prompt

logger = logging.getLogger(__name__)


class CvboostAgent:
    """简历优化专家 Agent — 单轮对话，直接调用 LLM 返回优化结果。"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY") or MODEL_API_KEY
        self.base_url = base_url or MODEL_BASE_URL
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        self.system_prompt = get_system_prompt()

    async def run(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        response = await self._call_llm(messages)
        return response.choices[0].message.content or ""

    async def run_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        async for event in self._call_llm_stream(messages):
            if event["type"] == "content":
                yield event["text"]

    async def _call_llm(self, messages: list[dict]):
        for attempt in range(LLM_MAX_RETRIES):
            try:
                extra_body = {}
                if not THINKING_ENABLED:
                    extra_body["thinking"] = {"type": "disabled"}
                return await self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    extra_body=extra_body,
                )
            except Exception as e:
                logger.warning("LLM call attempt %d failed: %s", attempt + 1, e)
                if attempt < LLM_MAX_RETRIES - 1:
                    time.sleep(LLM_RETRY_BACKOFF_BASE ** (attempt + 1))
                else:
                    raise

    async def _call_llm_stream(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        extra_body = {}
        if not THINKING_ENABLED:
            extra_body["thinking"] = {"type": "disabled"}
        response = await self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=True,
            extra_body=extra_body,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield {"type": "content", "text": delta.content}
