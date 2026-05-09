import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


@dataclass
class VisitRecord:
    ip_hash: str          # SHA256 哈希后的 IP（隐私保护）
    ip_prefix: str        # IP 前两段，用于粗略定位（如 119.45.x.x）
    path: str
    method: str
    user_agent: str
    referrer: str
    timestamp: datetime = field(default_factory=datetime.now)


class AnalyticsCollector:
    """内存中的访问统计收集器"""

    def __init__(self, max_records: int = 10000):
        self._visits: list[VisitRecord] = []
        self._max = max_records

    def record(self, visit: VisitRecord):
        self._visits.append(visit)
        if len(self._visits) > self._max:
            self._visits = self._visits[-self._max:]

    def stats(self) -> dict:
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        recent = [v for v in self._visits if v.timestamp >= last_24h]

        all_ips = set(v.ip_hash for v in self._visits)
        recent_ips = set(v.ip_hash for v in recent)

        path_counts = defaultdict(int)
        for v in self._visits:
            path_counts[v.path] += 1

        # 最近 20 条访问记录
        latest = sorted(recent, key=lambda v: v.timestamp, reverse=True)[:20]

        return {
            "totals": {
                "all_time_visits": len(self._visits),
                "all_time_unique_ips": len(all_ips),
                "last_24h_visits": len(recent),
                "last_24h_unique_ips": len(recent_ips),
            },
            "by_path": sorted(
                [{"path": p, "count": c} for p, c in path_counts.items()],
                key=lambda x: x["count"], reverse=True,
            ),
            "recent_visits": [
                {
                    "ip_prefix": v.ip_prefix,
                    "path": v.path,
                    "ua_short": v.user_agent[:80] if v.user_agent else "",
                    "referrer": v.referrer or "",
                    "time": v.timestamp.isoformat(),
                }
                for v in latest
            ],
        }


# 全局单例
collector = AnalyticsCollector()


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """在每个请求时记录访问信息"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 只记录页面和 API 访问，跳过静态资源
        if not path.startswith(("/api/", "/health")) and path not in ("", "/"):
            return await call_next(request)

        ip = self._get_ip(request)
        ua = request.headers.get("user-agent", "")
        referrer = request.headers.get("referer", "")

        visit = VisitRecord(
            ip_hash=self._hash_ip(ip),
            ip_prefix=self._prefix_ip(ip),
            path=path,
            method=request.method,
            user_agent=ua,
            referrer=referrer,
        )
        collector.record(visit)

        return await call_next(request)

    @staticmethod
    def _get_ip(request: Request) -> str:
        # Railway 等平台会通过代理转发，优先取 X-Forwarded-For
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # Cloudflare 等 CDN 的 header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _hash_ip(ip: str) -> str:
        return hashlib.sha256(f"cvboost_salt_{ip}".encode()).hexdigest()[:16]

    @staticmethod
    def _prefix_ip(ip: str) -> str:
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.x.x"
        return ip
