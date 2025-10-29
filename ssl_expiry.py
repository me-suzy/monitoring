from __future__ import annotations

from typing import Dict, Any
from urllib.parse import urlparse

from .common import append_markdown, check_ssl_expiry, now_iso, save_json, cfg


def run() -> Dict[str, Any]:
	host = urlparse(cfg.SITE_URL).hostname or ""
	days_left, error = check_ssl_expiry(host)
	result: Dict[str, Any] = {
		"host": host,
		"days_left": days_left,
		"error": error,
		"warn": (days_left is not None and days_left <= cfg.SSL_EXPIRY_WARN_DAYS) or error is not None,
		"timestamp": now_iso(),
	}
	save_json("ssl_expiry", result)
	status_line = f"- SSL: host={host} days_left={days_left} warn={result['warn']}"
	if error:
		status_line += f" error={error}"
	append_markdown("summary", status_line)
	return result


if __name__ == "__main__":
	print(run())


