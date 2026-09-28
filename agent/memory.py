"""Long-term memory: a MEMORY.md file the agent reads and appends to."""
from __future__ import annotations

import os
from datetime import date


def memory_path(memory_dir: str) -> str:
    return os.path.join(memory_dir, "MEMORY.md")


def ensure(memory_dir: str) -> str:
    os.makedirs(memory_dir, exist_ok=True)
    p = memory_path(memory_dir)
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write("# MEMORY.md\n\n"
                    "_Durable facts the agent should remember across conversations._\n")
    return p


def read_all(memory_dir: str) -> str:
    p = ensure(memory_dir)
    with open(p, encoding="utf-8") as f:
        return f.read()


def remember(memory_dir: str, fact: str) -> None:
    p = ensure(memory_dir)
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"\n- {date.today().isoformat()}: {fact.strip()}\n")


def recall(memory_dir: str, query: str, limit: int = 10) -> str:
    text = read_all(memory_dir)
    words = query.lower().split()
    scored = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("_"):
            continue
        score = sum(1 for w in words if w in line.lower())
        if score:
            scored.append((score, line))
    scored.sort(key=lambda x: -x[0])
    return "\n".join(line for _, line in scored[:limit]) or "no matching memories"
