from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.agent import CvboostAgent


def _fake_completion(content: str | None = None):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


class TestCvboostAgentCreation:
    def test_default_init_loads_system_prompt(self):
        agent = CvboostAgent(api_key="sk-test")
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0

    def test_custom_base_url(self):
        agent = CvboostAgent(api_key="sk-test", base_url="https://custom.api/v1")
        assert agent.base_url == "https://custom.api/v1"


class TestCvboostAgentRun:
    @pytest.mark.asyncio
    async def test_returns_llm_response(self):
        agent = CvboostAgent(api_key="sk-test")
        fake_resp = _fake_completion(content="这是优化后的简历...")

        with patch.object(agent, "_call_llm", AsyncMock(return_value=fake_resp)):
            result = await agent.run("请帮我优化简历")
            assert result == "这是优化后的简历..."

    @pytest.mark.asyncio
    async def test_sends_system_and_user_messages(self):
        agent = CvboostAgent(api_key="sk-test")
        captured_messages = []

        async def capture(msgs):
            captured_messages.extend(msgs)
            return _fake_completion(content="ok")

        with patch.object(agent, "_call_llm", capture):
            await agent.run("测试输入")

        assert captured_messages[0] == {"role": "system", "content": agent.system_prompt}
        assert captured_messages[1] == {"role": "user", "content": "测试输入"}


async def _fake_stream_content(text: str):
    yield {"type": "content", "text": text}


class TestCvboostAgentRunStream:
    @pytest.mark.asyncio
    async def test_stream_yields_content(self):
        agent = CvboostAgent(api_key="sk-test")

        with patch.object(
            agent, "_call_llm_stream",
            new=lambda msgs: _fake_stream_content("流式优化结果"),
        ):
            chunks = []
            async for chunk in agent.run_stream("优化简历"):
                chunks.append(chunk)
            assert chunks == ["流式优化结果"]
