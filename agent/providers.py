"""Model providers.

One OpenAI-compatible client covers OpenRouter, DeepSeek, Together, xAI,
Alibaba, Zhipu, Moonshot, Ollama (local), LM Studio, vLLM, and most other hosts.
"""
from __future__ import annotations

import httpx


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str,
                 app_name: str = "pocket-agent"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.app_name = app_name

    def chat(self, messages, tools=None, temperature: float = 0.7,
             max_tokens: int = 4096):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        # Harmless for non-OpenRouter hosts; OpenRouter uses them for attribution.
        headers["HTTP-Referer"] = "https://github.com/rawmware/pocket-agent"
        headers["X-Title"] = self.app_name

        payload = {"model": self.model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        with httpx.Client(timeout=180) as client:
            resp = client.post(f"{self.base_url}/chat/completions",
                               headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:500]
            raise RuntimeError(
                f"LLM request failed ({resp.status_code}): {detail}") from e

        data = resp.json()
        message = data["choices"][0]["message"]
        usage = data.get("usage") or {}
        return message, {"prompt_tokens": usage.get("prompt_tokens", 0),
                         "completion_tokens": usage.get("completion_tokens", 0)}
