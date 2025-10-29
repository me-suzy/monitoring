from __future__ import annotations

from typing import Dict, Any, List

from .common import append_markdown, http_request, now_iso, save_json, cfg


REQUIRED_HEADERS: List[str] = [
	"strict-transport-security",
	"x-content-type-options",
	"x-frame-options",
	"x-xss-protection",
	"content-security-policy",
]


def run() -> Dict[str, Any]:
	resp = http_request(cfg.SITE_URL)
	missing = [h for h in REQUIRED_HEADERS if h not in resp.headers]
	result: Dict[str, Any] = {
		"status": resp.status,
		"missing": missing,
		"ok": len(missing) == 0,
		"timestamp": now_iso(),
	}
	save_json("security_headers", result)
	append_markdown(
		"summary",
		f"- Security headers: status={resp.status} missing={len(missing)}"
	)
	return result


if __name__ == "__main__":
	print(run())


