from __future__ import annotations

from collections import deque
from typing import Dict, Any, List, Set

from .common import append_markdown, extract_links, http_request, is_allowed_url, now_iso, save_json, cfg


def run() -> Dict[str, Any]:
	start_url = cfg.SITE_URL
	queue: deque[str] = deque([start_url])
	visited: Set[str] = set()
	broken: List[Dict[str, Any]] = []
	count = 0

	while queue and count < cfg.MAX_PAGES_CRAWL:
		url = queue.popleft()
		if url in visited:
			continue
		visited.add(url)
		count += 1
		try:
			resp = http_request(url)
			if resp.status >= 400:
				broken.append({"url": url, "status": resp.status})
				continue
			for link in extract_links(resp.body, url):
				if is_allowed_url(link) and link not in visited:
					queue.append(link)
		except Exception as e:
			broken.append({"url": url, "error": str(e)})

	result: Dict[str, Any] = {
		"scanned": len(visited),
		"broken_count": len(broken),
		"broken": broken[:1000],  # cap
		"timestamp": now_iso(),
	}
	save_json("link_checker", result)
	append_markdown("summary", f"- Links: scanned={result['scanned']} broken={result['broken_count']}")
	return result


if __name__ == "__main__":
	print(run())


