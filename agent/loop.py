"""The agent loop: system prompt -> model -> tools -> model.

Includes a daily spend guard and conversation compaction so long chats
don't blow the context window (or the budget).
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime

from . import memory as M
from . import tools as T
from .config import load_settings
from .providers import OpenAICompatibleProvider

SYSTEM_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "system-prompt.md")


class BudgetExceeded(RuntimeError):
    pass


class Agent:
    def __init__(self, settings=None, model: str | None = None):
        self.s = settings or load_settings()
        self.model = model or self.s["default_model"]
        self.provider = OpenAICompatibleProvider(
            self.s["base_url"], self.s["api_key"], self.model)
        for d in (self.s["workspace"], self.s["memory_dir"], self.s["data_dir"]):
            os.makedirs(d, exist_ok=True)
        self.ctx = {"workspace": self.s["workspace"],
                    "memory_dir": self.s["memory_dir"],
                    "data_dir": self.s["data_dir"],
                    "tavily_key": self.s["tavily_key"]}

    # ----- prompt -----
    def system_prompt(self) -> str:
        if os.path.exists(SYSTEM_PATH):
            with open(SYSTEM_PATH, encoding="utf-8") as f:
                base = f.read()
        else:
            base = "You are a helpful personal AI agent with tools and long-term memory."
        mem = M.read_all(self.s["memory_dir"])
        return (base.replace("{{date}}", datetime.now().strftime("%A, %B %d, %Y"))
                    .replace("{{memory}}", mem[:6000]))

    # ----- budget -----
    def _spend_file(self) -> str:
        return os.path.join(self.s["data_dir"], "spend.json")

    def spent_today(self) -> float:
        try:
            with open(self._spend_file(), encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return 0.0
        return float(data.get(date.today().isoformat(), 0.0))

    def _record_spend(self, amount: float) -> None:
        p = self._spend_file()
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        k = date.today().isoformat()
        data[k] = round(float(data.get(k, 0.0)) + amount, 4)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def estimate_cost(self, usage: dict) -> float:
        per_mtok_in = float(os.getenv("PRICE_IN_PER_MTOK", "1.0"))
        per_mtok_out = float(os.getenv("PRICE_OUT_PER_MTOK", "3.0"))
        return (usage.get("prompt_tokens", 0) / 1e6 * per_mtok_in +
                usage.get("completion_tokens", 0) / 1e6 * per_mtok_out)

    def _guard(self, usage: dict) -> None:
        if self.spent_today() + self.estimate_cost(usage) > self.s["daily_budget"]:
            raise BudgetExceeded(
                f"Daily budget ${self.s['daily_budget']:.2f} would be exceeded "
                f"(spent ${self.spent_today():.2f} today). Raise DAILY_BUDGET_USD "
                f"or switch to a cheaper model.")

    # ----- compaction -----
    def _maybe_compact(self, messages: list) -> None:
        hist = messages[1:]
        if len(hist) <= 60:
            return
        old, keep = hist[:-20], hist[-20:]
        convo = "\n".join(
            f"{m.get('role')}: {str(m.get('content') or '')[:400]}" for m in old)
        msg, _ = self.provider.chat(
            [{"role": "user",
              "content": "Summarize this conversation in a few sentences. Keep key "
                         "facts, decisions, names, and open todos:\n\n" + convo[:12000]}],
            temperature=0.3, max_tokens=600)
        summary = (msg.get("content") or "").strip()
        messages[1:] = [{"role": "user",
                         "content": f"[Summary of earlier conversation: {summary}]"}] + keep

    # ----- main loop -----
    def run(self, user_text: str, history: list, on_event=None):
        base = self.s["base_url"]
        local = any(h in base for h in ("localhost", "127.0.0.1", "host.docker.internal"))
        if not self.s["api_key"] and not local:
            raise RuntimeError(
                "LLM_API_KEY is not set. Copy .env.example to .env and add a key "
                "(OpenRouter, DeepSeek, Together…), or point LLM_BASE_URL at a local Ollama.")

        messages = [{"role": "system", "content": self.system_prompt()}]
        messages += history[-40:]
        messages.append({"role": "user", "content": user_text})
        self._maybe_compact(messages)

        total = {"prompt_tokens": 0, "completion_tokens": 0}
        for _ in range(self.s["max_steps"]):
            self._guard(total)
            msg, usage = self.provider.chat(messages, tools=T.SCHEMAS)
            total["prompt_tokens"] += usage["prompt_tokens"]
            total["completion_tokens"] += usage["completion_tokens"]

            calls = msg.get("tool_calls") or []
            assistant = {"role": "assistant", "content": msg.get("content") or ""}
            if calls:
                assistant["tool_calls"] = calls
            messages.append(assistant)

            if not calls:
                reply = msg.get("content") or ""
                cost = self.estimate_cost(total)
                self._record_spend(cost)
                new_history = history + [{"role": "user", "content": user_text},
                                         {"role": "assistant", "content": reply}]
                return reply, new_history, total, cost

            for call in calls:
                name = call["function"]["name"]
                try:
                    args = json.loads(call["function"].get("arguments") or "{}")
                except Exception:
                    args = {}
                if on_event:
                    on_event({"event": "tool", "name": name, "args": args})
                try:
                    result = T.execute(name, args, self.ctx)
                except Exception as e:
                    result = f"error: {e}"
                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": T.truncate(result)})
        raise RuntimeError(
            f"Stopped after {self.s['max_steps']} tool steps without a final answer.")
