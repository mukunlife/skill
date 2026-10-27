"""按当前 Claude Code 配置发一次最小请求，核验实际使用的服务端。

只读取 ~/.claude/settings.json 中的 env，不打印密钥；
输出写入同目录 api_probe.json，密钥字段固定为 REDACTED。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "settings.json"
OUT = Path(__file__).resolve().parent / "api_probe.json"


def main() -> int:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    env = settings.get("env", {})
    base_url = env.get("ANTHROPIC_BASE_URL", "").rstrip("/")
    token = env.get("ANTHROPIC_AUTH_TOKEN", "")
    model = env.get("ANTHROPIC_MODEL", "")
    if not (base_url and token and model):
        print("[失败] settings.json 缺少 BASE_URL / AUTH_TOKEN / MODEL")
        return 2

    payload = {
        "model": model,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "只回复四个字：连接成功"}],
    }
    request = urllib.request.Request(
        f"{base_url}/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": token,
            "authorization": f"Bearer {token}",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    record = {
        "base_url": base_url,
        "model_configured": model,
        "auth_token": "REDACTED",
        "request_path": "/v1/messages",
    }
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
            record.update(
                {
                    "http_status": response.status,
                    "server_header": response.headers.get("server"),
                    "response_model": body.get("model"),
                    "content": [
                        block.get("text", "")
                        for block in body.get("content", [])
                        if isinstance(block, dict)
                    ],
                }
            )
    except urllib.error.HTTPError as exc:
        record.update(
            {
                "http_status": exc.code,
                "error": exc.read().decode("utf-8", errors="replace")[:500],
            }
        )
    except Exception as exc:  # noqa: BLE001 - 记录网络错误即可
        record.update({"error": f"{type(exc).__name__}: {exc}"})

    OUT.write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record.get("http_status") == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
