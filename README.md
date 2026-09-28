# 🤖 Pocket Agent

Your own personal AI agent that runs anywhere. Chat with it from any device, give it tools
(shell, files, web), long-term memory, and plug in whatever language model you want —
including models that cost a fraction of a cent per conversation.

This replicates **the experience of using a personal AI agent** (like Muse): a chat UI,
an agent that can actually *do* things on a computer, memory across conversations, and
access from your phone. It is not Muse itself — see [What this is not](#what-this-is-not).

## Quickstart

```bash
git clone https://github.com/rawmware/pocket-agent
cd pocket-agent
cp .env.example .env        # add one API key (OpenRouter, DeepSeek, etc.)
pip install -r requirements.txt
python server.py
```

Open http://localhost:8000 — on your phone, use your computer's LAN address
(e.g. `http://192.168.1.5:8000`) and **Add to Home Screen** for an app-like feel.

Or with Docker:

```bash
docker compose up --build
```

## How it maps to "how you use Muse"

| What you get from Muse | How Pocket Agent does it |
|---|---|
| Chat from any device | Mobile-friendly web UI (`web/index.html`), served by `server.py` |
| Agent that uses tools | `agent/loop.py` + `agent/tools.py`: shell, files, web fetch/search, todos |
| Remembers you | `memory/MEMORY.md` + `remember`/`recall` tools |
| Usage limits | **You** set `DAILY_BUDGET_USD` — the agent stops itself at your cap |
| Always-on computer | Docker, Raspberry Pi, or a cheap VPS (see `docs/DEVICES.md`) |
| Model choice | Any OpenAI-compatible API: OpenRouter, DeepSeek, Together, Ollama… |

## Cost: the whole point

There is no subscription. You pay the model provider per token, and you pick the model.

| Model (Sep 2026 prices) | Input / 1M tokens | Output / 1M tokens |
|---|---|---|
| DeepSeek V4 Flash (off-peak) | $0.14 | $0.28 |
| DeepSeek V4 Pro | $0.435 | $0.87 |
| gpt-oss-120b (cheap hosts) | $0.03 | $0.17 |
| GLM-5.2 | $1.40 | $4.40 |
| Kimi K3 (agent specialist) | $3.00 | $15.00 |
| Claude Sonnet 5 | $2.00 | $10.00 |
| Ollama (run locally) | $0 | $0 |

*Prices move — check `docs/COSTS.md` for sources and the current table.*

Rough math: a typical agent reply burns ~2k input + 1k output tokens. On DeepSeek V4
Flash that's about **a tenth of a cent per reply** — thousands of conversations per dollar.
The default `DAILY_BUDGET_USD=2.00` is generous; most days you'll spend pennies.

**Cheapest serious setup:** one [OpenRouter](https://openrouter.ai) key ($10 credit lasts
ages), `DEFAULT_MODEL=deepseek/deepseek-chat`. **Free setup:** Ollama on your computer,
`LLM_BASE_URL=http://localhost:11434/v1`, no key at all.

## Repo layout

```
pocket-agent/
├── server.py            # FastAPI server: chat UI + /api/chat (SSE)
├── web/index.html       # single-file mobile-friendly chat UI
├── agent/
│   ├── loop.py          # the agent loop: prompt → model → tools → model
│   ├── providers.py     # OpenAI-compatible provider (OpenRouter, DeepSeek, Ollama…)
│   ├── tools.py         # shell, files, web, memory, todos (jailed to workspace/)
│   ├── memory.py        # MEMORY.md read/append/search
│   └── config.py        # settings from environment / .env
├── config/system-prompt.md  # the agent's persona — edit freely
├── memory/MEMORY.md     # long-term memory seed
├── docs/
│   ├── COSTS.md         # model price table + budget math
│   ├── MODELS.md        # which model for which job, how to switch
│   └── DEVICES.md       # run it on iPhone, Android, Pi, VPS, free hosts
├── Dockerfile / docker-compose.yml
└── .env.example
```

## What this is not

- **Not Muse itself.** There is no public "Muse agent API key" — Muse is Meta's consumer
  app (powered by Muse Spark). The closest developer route to Muse models is the
  Meta Model API at dev.meta.ai. This repo gives you the *agent harness*; the brain is
  whatever model you plug in.
- **Not as smart out of the box.** A $0.30/MTok model won't match a frontier agent on
  hard tasks. That's what `SMART_MODEL` is for — pick it in the UI (🧠) when a task is
  genuinely hard, stay on ⚡ for everything else.
- **V1 security.** File/shell tools are jailed to `workspace/`, destructive command
  patterns are blocked, but don't expose this to the public internet without putting it
  behind Tailscale or a reverse proxy with auth (see `docs/DEVICES.md`).

## Roadmap ideas

- Voice input in the web UI
- Scheduled tasks (cron-style background jobs)
- Image input for screenshots
- Anthropic-native provider (Claude models work today via OpenRouter)

PRs welcome.
