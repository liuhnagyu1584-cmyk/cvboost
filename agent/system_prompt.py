from functools import lru_cache
from pathlib import Path

_SKILL_PATH = Path(__file__).parent / "system_prompt.md"


@lru_cache(maxsize=1)
def get_system_prompt() -> str:
    """读取 system_prompt.md，模块级缓存只读一次。"""
    return _SKILL_PATH.read_text(encoding="utf-8")
