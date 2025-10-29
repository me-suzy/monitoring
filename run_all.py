from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from . import config as cfg
from .common import append_markdown, ensure_report_dir, now_iso, save_json
from . import uptime_check, ssl_expiry, sitemap_robots, link_checker, security_headers


def run_all() -> Dict[str, Any]:
	report_dir = ensure_report_dir()
	append_markdown("summary", f"\n## Site monitoring report for {cfg.SITE_URL} ({now_iso()})\n")

	uptime = uptime_check.run()
	ssl_res = ssl_expiry.run()
	rob = sitemap_robots.run()
	links = link_checker.run()
	sec = security_headers.run()

	aggregate: Dict[str, Any] = {
		"site": cfg.SITE_URL,
		"uptime": uptime,
		"ssl": ssl_res,
		"robots": rob,
		"links": links,
		"security": sec,
		"timestamp": now_iso(),
	}
	save_json("aggregate", aggregate)
	append_markdown(
		"summary",
		"\nDone. See JSON files for detailed results.\n"
	)
	return aggregate


if __name__ == "__main__":
	res = run_all()
	print(json.dumps(res, indent=2))


