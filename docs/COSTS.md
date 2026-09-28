# Costs

No subscription, no seat license. You pay a model provider per token, and you choose
the model. Prices below are per **1M tokens**, checked **September 2026** — they move,
so treat this as a map, not a contract.

## The cheap tier (everyday agent work)

| Model | Input | Output | Notes |
|---|---|---|---|
| DeepSeek V4 Flash (off-peak) | $0.14 | $0.28 | Cheapest frontier-adjacent; 2x at peak hours |
| gpt-oss-120b (budget hosts) | $0.03 | $0.17 | Open weights; price varies by host |
| DeepSeek V4 Pro | $0.435 | $0.87 | Stronger, still under $1 |
| Qwen3-Coder-Next | $0.11 | $0.80 | Great for code tasks |
| MiniMax M3 | $0.30 | $1.20 | Fast budget option |

## The smart tier (hard tasks — pick 🧠 in the UI)

| Model | Input | Output | Notes |
|---|---|---|---|
| GLM-5.2 / 5.3 | $1.40 | $4.40 | Strong long-horizon agent runs, MIT weights |
| Kimi K3 | $3.00 | $15.00 | Tuned for agent harnesses, open weights |
| Claude Sonnet 5 | $2.00 | $10.00 | The reliable default "smart" pick |
| Gemini 3.8 Flash | $0.75 | $3.75 | Intro pricing through Dec 31, 2026 |

## Free tier

Ollama on your own machine: `$0.00`. Small local models are fine for simple Q&A but
noticeably weaker at multi-step tool use. Best as a $0 fallback, not the daily driver.

## Budget math

A typical agent reply uses roughly 2k input + 1k output tokens (more if it calls
several tools). Examples on DeepSeek V4 Flash off-peak:

- One reply: ~$0.0006 (six-hundredths of a cent)
- 100 replies/day: ~$0.06
- The default `DAILY_BUDGET_USD=2.00`: ~3,000+ replies before the agent stops itself

The server shows the estimated cost of every reply and today's total. The budget
guard uses `PRICE_IN_PER_MTOK` / `PRICE_OUT_PER_MTOK` from `.env` — set them to your
model's real prices so the math stays honest.

## How to pay the least

1. **One OpenRouter key** — access to every model above with a single $10 credit.
2. **DeepSeek direct** (api.deepseek.com) — cheaper than OpenRouter resale, and
   off-peak is half price. Use `LLM_BASE_URL=https://api.deepseek.com` and
   `DEFAULT_MODEL=deepseek-chat`.
3. **Route by difficulty** — ⚡ cheap model for chat and simple tasks, 🧠 smart model
   only when stuck. The UI model picker does exactly this.
4. **Cache-friendly habits** — the system prompt and memory are re-sent every turn;
   providers with prompt caching (DeepSeek's cache-hit input is ~$0.003/M) make long
   conversations nearly free on the input side.

## Sources

- Price comparison wiki (DeepSeek/GLM/Qwen/Kimi official rates):
  https://github.com/unclehobbot/aiwiki/blob/HEAD/wiki/models/llm-wiki-chinese-models-comparison.md
- Morph ranking with per-task cost (Sep 2026): https://www.morphllm.com/best-ai-model-for-coding
- Open-source coding models head-to-head:
  https://dev.to/shaam_ai/best-open-source-llm-for-coding-in-2026-qwen3-coder-vs-glm-52-vs-deepseek-v4-flash-19la
- Cheapest-host tracker: https://github.com/tokencanopy/price/blob/HEAD/README.md
