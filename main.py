"""
cvboost API — 简历优化专家 FastAPI 服务
启动: uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""
import logging
import os
import tempfile
from typing import AsyncGenerator

# 开启 INFO 级别日志，终端可见每个流式 token
logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from agent.agent import CvboostAgent
from agent.analytics import AnalyticsMiddleware, collector
from agent.config import (
    MODEL_NAME,
    SUCCESS_ACCURACY,
    SUCCESS_LATENCY_MS,
    SUCCESS_CONCURRENT_USERS,
)

app = FastAPI(title="cvboost", description="简历优化专家 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AnalyticsMiddleware)


# ── Request / Response models ──────────────────────────────────────

class OptimizeRequest(BaseModel):
    resume_text: str
    modules: list[str] | None = None
    job_description: str | None = None
    industry: str | None = None


class OptimizeResponse(BaseModel):
    success: bool
    report: str


# ── Prompt building ────────────────────────────────────────────────

def build_prompt(req: OptimizeRequest) -> str:
    parts: list[str] = []

    if req.job_description:
        parts.append(f"目标岗位 JD 如下：\n{req.job_description}\n")

    if req.industry:
        parts.append(f"目标行业：{req.industry}")

    if req.modules:
        modules_str = "、".join(req.modules)
        parts.append(f"请帮我优化以下简历的【{modules_str}】模块：\n{req.resume_text}")
    else:
        parts.append(f"请帮我优化以下简历（全简历）：\n{req.resume_text}")

    return "\n".join(parts)


# ── API routes ─────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "sla": {
            "accuracy": SUCCESS_ACCURACY,
            "latency_ms": SUCCESS_LATENCY_MS,
            "concurrent_users": SUCCESS_CONCURRENT_USERS,
        },
    }


@app.get("/api/v1/analytics")
async def analytics():
    """返回访问统计数据"""
    return collector.stats()


@app.post("/api/v1/analytics/track")
async def analytics_track(request: Request):
    """前端埋点：记录页面访问事件"""
    return {"ok": True}


@app.get("/")
async def index():
    """提供前端 Demo 页面"""
    return FileResponse("static/index.html")


@app.post("/api/v1/optimize", response_model=OptimizeResponse)
async def optimize(req: OptimizeRequest):
    if not req.resume_text.strip():
        raise HTTPException(status_code=400, detail="简历内容不能为空")

    agent = CvboostAgent()
    prompt = build_prompt(req)

    try:
        report = await agent.run(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化失败：{e}")

    return OptimizeResponse(success=True, report=report)


@app.post("/api/v1/optimize/stream")
async def optimize_stream(req: OptimizeRequest):
    if not req.resume_text.strip():
        raise HTTPException(status_code=400, detail="简历内容不能为空")

    agent = CvboostAgent()
    prompt = build_prompt(req)

    async def generate() -> AsyncGenerator[str, None]:
        try:
            async for chunk in agent.run_stream(prompt):
                yield chunk
        except Exception as e:
            yield f"\n[错误] {e}"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@app.post("/api/v1/optimize/file")
async def optimize_file(file: UploadFile = File(...)):
    allowed = {".pdf", ".docx", ".doc"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}。支持：{', '.join(allowed)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from agent.parse_resume import parse_resume
        resume_text = await parse_resume(tmp_path)
    finally:
        os.unlink(tmp_path)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="未能从文件中提取文本内容")

    agent = CvboostAgent()
    prompt = f"请帮我优化以下简历（全简历）：\n{resume_text}"

    try:
        report = await agent.run(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化失败：{e}")

    return OptimizeResponse(success=True, report=report)


@app.post("/api/v1/optimize/file/stream")
async def optimize_file_stream(
    file: UploadFile = File(...),
):
    """上传简历文件，解析文本后流式返回优化结果"""
    # ── 校验文件格式 ──
    allowed = {".pdf", ".docx", ".doc"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}。支持：{', '.join(allowed)}",
        )

    # ── 将上传文件写入临时磁盘文件，供解析器读取 ──
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # ── 解析文件中的简历文本，用完立即清理临时文件 ──
    try:
        from agent.parse_resume import parse_resume
        resume_text = await parse_resume(tmp_path)
    finally:
        os.unlink(tmp_path)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="未能从文件中提取文本内容")

    # ── 构造 prompt 并启动流式 LLM 调用 ──
    agent = CvboostAgent()
    prompt = f"请帮我优化以下简历（全简历）：\n{resume_text}"

    async def generate() -> AsyncGenerator[str, None]:
        try:
            async for chunk in agent.run_stream(prompt):
                yield chunk
        except Exception as e:
            yield f"\n[错误] {e}"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
