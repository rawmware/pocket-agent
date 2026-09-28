"""Built-in tools. File operations are jailed to the workspace directory."""
from __future__ import annotations

import html as htmlmod
import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime

from . import memory as M

MAX_OUT = 8000
FETCH_MAX = 12000


def truncate(s: str, n: int = MAX_OUT) -> str:
    s = str(s)
    return s if len(s) <= n else s[:n] + f"\n…[truncated {len(s) - n} chars]"


def _safe_path(workspace: str, path: str) -> str:
    p = os.path.abspath(os.path.join(workspace, path or "."))
    if p != workspace and not p.startswith(workspace + os.sep):
        raise ValueError("path escapes the workspace")
    return p


# Commands matching these patterns are refused outright.
DENY = [
    r"rm\s+-rf\s+/", r":\(\)\s*\{", r"mkfs(\.| )", r"\bdd\s+if=",
    r">\s*/dev/(sd|hd|nvme)", r"\bshutdown\b", r"\breboot\b",
]


def _check_cmd(cmd: str) -> None:
    for pat in DENY:
        if re.search(pat, cmd):
            raise ValueError("blocked: dangerous command pattern")


def _read_file(ctx, args):
    p = _safe_path(ctx["workspace"], args["path"])
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return truncate(f.read(), 20000)


def _write_file(ctx, args):
    p = _safe_path(ctx["workspace"], args["path"])
    parent = os.path.dirname(p)
    os.makedirs(parent or ctx["workspace"], exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(args.get("content", ""))
    return f"wrote {len(args.get('content', ''))} chars to {args['path']}"


def _edit_file(ctx, args):
    p = _safe_path(ctx["workspace"], args["path"])
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    old = args["old_text"]
    if old not in text:
        return "error: old_text not found in file"
    text = text.replace(old, args["new_text"], 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return "edit applied"


def _list_dir(ctx, args):
    p = _safe_path(ctx["workspace"], args.get("path", "."))
    items = sorted(os.listdir(p))
    out = [("dir  " if os.path.isdir(os.path.join(p, i)) else "file ") + i
           for i in items]
    return "\n".join(out) or "(empty)"


def _exec(ctx, args):
    cmd = args["command"]
    _check_cmd(cmd)
    timeout = min(int(args.get("timeout", 60)), 600)
    proc = subprocess.run(cmd, shell=True, cwd=ctx["workspace"],
                          capture_output=True, text=True, timeout=timeout)
    out = (proc.stdout or "") + (proc.stderr or "")
    return f"exit={proc.returncode}\n" + truncate(out.strip() or "(no output)")


def _web_fetch(ctx, args):
    url = args["url"]
    if not re.match(r"^https?://", url):
        raise ValueError("only http(s) URLs allowed")
    req = urllib.request.Request(url, headers={"User-Agent": "pocket-agent/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read(200_000).decode("utf-8", "replace")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw,
                  flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = htmlmod.unescape(text)
    return truncate(re.sub(r"\s+", " ", text).strip(), FETCH_MAX)


def _web_search(ctx, args):
    key = ctx.get("tavily_key", "")
    if not key:
        return ("web search is not configured (set TAVILY_API_KEY). "
                "I can still fetch a URL directly with web_fetch.")
    payload = json.dumps({"api_key": key, "query": args["query"],
                          "max_results": 5, "include_answer": True}).encode()
    req = urllib.request.Request("https://api.tavily.com/search", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    lines = []
    if data.get("answer"):
        lines.append("Answer: " + data["answer"])
    for res in data.get("results", []):
        lines.append(f"- {res.get('title')}: {res.get('url')}\n"
                     f"  {str(res.get('content', ''))[:400]}")
    return "\n".join(lines) or "no results"


def _remember(ctx, args):
    M.remember(ctx["memory_dir"], args["fact"])
    return "remembered"


def _recall(ctx, args):
    return M.recall(ctx["memory_dir"], args["query"])


def _todos_path(ctx):
    return os.path.join(ctx["memory_dir"], "todos.json")


def _load_todos(ctx):
    try:
        with open(_todos_path(ctx), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_todos(ctx, todos):
    with open(_todos_path(ctx), "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2)


def _todo_add(ctx, args):
    todos = _load_todos(ctx)
    todos.append({"text": args["text"], "done": False})
    _save_todos(ctx, todos)
    return f"added todo #{len(todos)}"


def _todo_list(ctx, args):
    todos = _load_todos(ctx)
    if not todos:
        return "(no todos)"
    return "\n".join(
        f"[{'x' if t['done'] else ' '}] #{i + 1} {t['text']}"
        for i, t in enumerate(todos))


def _todo_done(ctx, args):
    todos = _load_todos(ctx)
    i = int(args["index"]) - 1
    if not 0 <= i < len(todos):
        return "error: bad index"
    todos[i]["done"] = True
    _save_todos(ctx, todos)
    return f"marked todo #{i + 1} done"


def _get_time(ctx, args):
    return datetime.now().strftime("%A, %B %d, %Y %I:%M %p")


def _fn(name, desc, params, required=()):
    return {"type": "function",
            "function": {"name": name, "description": desc,
                         "parameters": {"type": "object",
                                        "properties": params,
                                        "required": list(required)}}}


def _s(desc=""):
    return {"type": "string", "description": desc}


SCHEMAS = [
    _fn("get_time", "Current local date and time.", {}),
    _fn("read_file", "Read a text file from the workspace.",
        {"path": _s("relative path")}, ["path"]),
    _fn("write_file", "Write (create or overwrite) a text file in the workspace.",
        {"path": _s("relative path"), "content": _s("file content")},
        ["path", "content"]),
    _fn("edit_file", "Replace the first occurrence of old_text with new_text in a file.",
        {"path": _s("relative path"), "old_text": _s("exact text to find"),
         "new_text": _s("replacement text")}, ["path", "old_text", "new_text"]),
    _fn("list_dir", "List a workspace directory.",
        {"path": _s("relative path, default '.'")}),
    _fn("exec", "Run a shell command inside the workspace. No sudo; destructive patterns are blocked.",
        {"command": _s("shell command"), "timeout": {"type": "integer",
         "description": "seconds, default 60, max 600"}}, ["command"]),
    _fn("web_fetch", "Fetch a URL and return its text content.",
        {"url": _s("http(s) URL")}, ["url"]),
    _fn("web_search", "Search the web. Needs TAVILY_API_KEY, otherwise returns a notice.",
        {"query": _s("search query")}, ["query"]),
    _fn("remember", "Save a durable fact to long-term memory.",
        {"fact": _s("fact to remember")}, ["fact"]),
    _fn("recall", "Search long-term memory.",
        {"query": _s("search terms")}, ["query"]),
    _fn("todo_add", "Add an item to the todo list.",
        {"text": _s("todo text")}, ["text"]),
    _fn("todo_list", "List all todos.", {}),
    _fn("todo_done", "Mark a todo done by its number.",
        {"index": {"type": "integer", "description": "todo number from todo_list"}},
        ["index"]),
]

HANDLERS = {
    "get_time": _get_time, "read_file": _read_file, "write_file": _write_file,
    "edit_file": _edit_file, "list_dir": _list_dir, "exec": _exec,
    "web_fetch": _web_fetch, "web_search": _web_search, "remember": _remember,
    "recall": _recall, "todo_add": _todo_add, "todo_list": _todo_list,
    "todo_done": _todo_done,
}


def execute(name: str, args: dict, ctx: dict) -> str:
    fn = HANDLERS.get(name)
    if not fn:
        return f"error: unknown tool {name}"
    return fn(ctx, args or {})
