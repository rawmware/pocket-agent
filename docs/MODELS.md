# Models

Pocket Agent talks to any **OpenAI-compatible** chat-completions API. That covers
practically every provider: OpenRouter, DeepSeek, Together, xAI, Alibaba, Zhipu,
Moonshot, Ollama, LM Studio, vLLM… If it speaks `/chat/completions`, it works.

## What makes a good agent model

1. **Reliable tool calling** — follows the function schema, doesn't hallucinate
   parameters, handles 10–30 sequential tool rounds without losing the plot.
2. **Long context** — the system prompt + memory + conversation + tool outputs add up.
3. **Instruction following** — actually does what the system prompt says.
4. **Price** — the agent loop is token-hungry; per-token price dominates the bill.

## Recommended setups

**Cheapest serious (recommended default)**
```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-...
DEFAULT_MODEL=deepseek/deepseek-chat
```
One $10 OpenRouter credit lasts months of daily use. Swap `DEFAULT_MODEL` to any slug
on openrouter.ai/models — e.g. `qwen/qwen3-coder-next`, `minimax/minimax-m3`.

**Even cheaper (DeepSeek direct)**
```env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-...
DEFAULT_MODEL=deepseek-chat
```
Cuts out the reseller margin; off-peak hours are half price.

**Best agent behavior (smart tier)**
```env
SMART_MODEL=moonshotai/kimi-k3
# or: z-ai/glm-5.2, anthropic/claude-sonnet-4-5 …
```
Pick 🧠 in the UI for hard coding or reasoning tasks, ⚡ for everything else.

**Free (local)**
```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=
DEFAULT_MODEL=qwen3:32b
```
Run `ollama pull qwen3:32b` first. $0 per token, private, works offline. Weaker at
long tool chains — fine for chat and simple file tasks.

## Notes

- Anthropic models work through OpenRouter (`anthropic/claude-sonnet-4-5`) — there is
  no separate Anthropic-native provider in v1.
- Model slugs change as providers ship new versions. If a slug 404s, check
  openrouter.ai/models for the current name.
- Vision/image input isn't wired up yet (see README roadmap).
