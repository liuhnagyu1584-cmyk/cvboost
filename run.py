"""临时测试脚本 — 直接调用 CvboostAgent，分别演示流式输出和整体输出"""
import asyncio
import sys
from agent.agent import CvboostAgent

SAMPLE_INPUT = """张三
3年Java开发经验，熟悉Spring Boot和MySQL。
参与过电商系统开发，负责订单模块。
期望薪资：15k
教育背景：某大学计算机本科"""


async def run_normal(agent: CvboostAgent, prompt: str):
    print("=" * 60)
    print("【整体输出模式】\n")
    result = await agent.run(prompt)
    print(result)
    print("\n" + "=" * 60)


async def run_stream(agent: CvboostAgent, prompt: str):
    print("=" * 60)
    print("【流式输出模式】\n")
    async for chunk in agent.run_stream(prompt):
        print(chunk, end="", flush=True)
    print("\n" + "=" * 60)


async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "stream"
    prompt = f"请帮我优化以下简历：\n{SAMPLE_INPUT}"

    agent = CvboostAgent()

    if mode == "normal":
        await run_normal(agent, prompt)
    elif mode == "stream":
        await run_stream(agent, prompt)
    else:
        print(f"用法: python run.py [stream|normal]")
        print(f"  stream  — 流式输出（默认）")
        print(f"  normal  — 完整输出")


if __name__ == "__main__":
    asyncio.run(main())
