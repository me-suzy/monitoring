from __future__ import annotations

import re
from typing import Dict, Any, List
from urllib.parse import urljoin

from .common import append_markdown, http_request, now_iso, save_json, cfg


def run() -> Dict[str, Any]:
	base = cfg.SITE_URL.rstrip("/")
	robots_url = urljoin(base + "/", "robots.txt")
	robots = http_request(robots_url)

	sitemaps: List[str] = []
	if robots.status == 200:
		text = robots.body.decode("utf-8", errors="ignore")
		for line in text.splitlines():
			m = re.match(r"(?i)^sitemap:\s*(\S+)", line.strip())
			if m:
				sitemaps.append(m.group(1))

	issues: List[str] = []
	if robots.status >= 400:
		issues.append(f"robots.txt status {robots.status}")

	# Validate first sitemap (basic status)
	sitemap_status = None
	if sitemaps:
		sm = http_request(sitemaps[0])
		sitemap_status = sm.status
		if sm.status >= 400:
			issues.append(f"sitemap status {sm.status}")

	result: Dict[str, Any] = {
		"robots_url": robots_url,
		"robots_status": robots.status,
		"sitemaps": sitemaps,
		"sitemap_status": sitemap_status,
		"issues": issues,
		"timestamp": now_iso(),
	}
	save_json("sitemap_robots", result)
	append_markdown(
		"summary",
		f"- Robots/Sitemap: robots={robots.status} sitemaps={len(sitemaps)} sitemap_status={sitemap_status} issues={len(issues)}"
	)
	return result


if __name__ == "__main__":
	print(run())


