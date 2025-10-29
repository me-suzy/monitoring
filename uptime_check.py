from __future__ import annotations

from typing import Dict, Any

from .common import HttpResponse, append_markdown, http_request, now_iso, save_json, cfg


def run() -> Dict[str, Any]:
	resp: HttpResponse = http_request(cfg.SITE_URL)
	result: Dict[str, Any] = {
		"url": cfg.SITE_URL,
		"status": resp.status,
		"elapsed_ms": round(resp.elapsed_ms, 2),
		"ok": 200 <= resp.status < 400,
		"warning": resp.elapsed_ms >= cfg.TTFB_WARNING_MS,
		"timestamp": now_iso(),
	}
	save_json("uptime", result)
	append_markdown(
		"summary",
		f"- Uptime: status={result['status']} elapsed={result['elapsed_ms']}ms ok={result['ok']} warning={result['warning']}"
	)
	return result


if __name__ == "__main__":
	res = run()
	print(res)


