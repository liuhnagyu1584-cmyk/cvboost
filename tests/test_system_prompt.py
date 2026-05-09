import pytest
from agent.system_prompt import get_system_prompt


class TestSystemPrompt:
    def test_loads_and_contains_key_sections(self):
        prompt = get_system_prompt()
        assert "简历优化专家" in prompt
        assert "核心规则" in prompt
        assert "输出规范" in prompt
        assert "异常处理" in prompt

    def test_does_not_contain_tool_or_rag_sections(self):
        prompt = get_system_prompt()
        assert "工具使用手册" not in prompt
        assert "知识检索规则" not in prompt
        assert "记忆策略" not in prompt

    def test_lru_cache_returns_same_instance(self):
        p1 = get_system_prompt()
        p2 = get_system_prompt()
        assert p1 is p2
