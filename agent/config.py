"""Runtime settings loaded from environment (.env supported)."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def load_settings() -> dict:
    get = os.getenv
    default_model = get("DEFAULT_MODEL", "deepseek/deepseek-chat")
    return {
        "base_url": get("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/"),
        "api_key": get("LLM_API_KEY", ""),
        "default_model": default_model,
        "smart_model": get("SMART_MODEL", "") or default_model,
        "workspace": os.path.abspath(get("WORKSPACE_DIR", "./workspace")),
        "memory_dir": os.path.abspath(get("MEMORY_DIR", "./memory")),
        "data_dir": os.path.abspath(get("DATA_DIR", "./data")),
        "daily_budget": float(get("DAILY_BUDGET_USD", "2.0") or 2.0),
        "max_steps": int(get("MAX_TOOL_STEPS", "25") or 25),
        "tavily_key": get("TAVILY_API_KEY", ""),
    }
