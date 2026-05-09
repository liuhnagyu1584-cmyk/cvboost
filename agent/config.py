from dotenv import load_dotenv

load_dotenv()

# ── Model Config ─────────────────────────────────────────────────────
MODEL_PROVIDER: str = "deepseek"
MODEL_NAME: str = "deepseek-v4-pro"
MODEL_BASE_URL: str = "https://api.deepseek.com"
MODEL_API_KEY: str = ""  # Set via env: DEEPSEEK_API_KEY
THINKING_ENABLED: bool = False # 是否开启思考模式

# ── LLM Call Config ──────────────────────────────────────────────────
LLM_TIMEOUT_SECONDS: int = 60
LLM_MAX_RETRIES: int = 3
LLM_RETRY_BACKOFF_BASE: float = 2.0

# ── Success Criteria (for /health endpoint) ──────────────────────────
SUCCESS_ACCURACY: float = 0.90 # 成功率阈值
SUCCESS_LATENCY_MS: int = 3000 # 响应时间阈值（毫秒）
SUCCESS_CONCURRENT_USERS: int = 10 # 并发用户数阈值
