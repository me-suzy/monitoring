from __future__ import annotations

import dataclasses
import json
import os
import re
import ssl as ssl_module
import sys
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import http.client


class _Defaults:
	SITE_URL = "https://neculaifantanaru.com"
	REQUEST_TIMEOUT_SECONDS = 20
	MAX_PAGES_CRAWL = 200
	ALLOWED_HOSTS = ["neculaifantanaru.com", "www.neculaifantanaru.com"]
	USER_AGENT = "SiteMonitor/1.0 (+https://github.com/me-suzy/Proiect-action-GitHub)"
	REPORT_DIR = ".reports"
	TTFB_WARNING_MS = 800
	SSL_EXPIRY_WARN_DAYS = 15


# Build a config object that overlays user config over defaults
class cfg:  # type: ignore
	pass

for k, v in _Defaults.__dict__.items():
	if k.isupper():
		setattr(cfg, k, v)

try:  # optional user config
	import monitoring.config as _user_cfg  # type: ignore
	import sys
	# The workflow creates a stub config.py, make sure it doesn't shadow our defaults
	if '_user_cfg' in sys.modules:
		for k, v in _user_cfg.__dict__.items():
			if k.isupper() and hasattr(cfg, k):
				setattr(cfg, k, v)
except Exception:
	pass


@dataclasses.dataclass
class HttpResponse:
	status: int
	headers: Dict[str, str]
	body: bytes
	elapsed_ms: float
	final_url: str


def ensure_report_dir() -> Path:
	report_dir = Path(__file__).resolve().parent / cfg.REPORT_DIR
	report_dir.mkdir(parents=True, exist_ok=True)
	return report_dir


def save_json(name: str, data: Dict[str, Any]) -> Path:
	dir_path = ensure_report_dir()
	path = dir_path / f"{name}.json"
	path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
	return path


def append_markdown(name: str, content: str) -> Path:
	dir_path = ensure_report_dir()
	path = dir_path / f"{name}.md"
	with open(path, "a", encoding="utf-8") as f:
		f.write(content)
		if not content.endswith("\n"):
			f.write("\n")
	return path


def normalize_headers(headers: Iterable[Tuple[str, str]]) -> Dict[str, str]:
	return {k.lower(): v for k, v in headers}


def http_request(url: str, *, method: str = "GET", timeout: Optional[int] = None, headers: Optional[Dict[str, str]] = None) -> HttpResponse:
	parsed = urllib.parse.urlparse(url)
	if parsed.scheme not in ("http", "https"):
		raise ValueError("Unsupported scheme")

	conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
	port = parsed.port or (443 if parsed.scheme == "https" else 80)
	path = parsed.path or "/"
	if parsed.query:
		path += f"?{parsed.query}"

	headers = headers or {}
	headers.setdefault("User-Agent", cfg.USER_AGENT)

	conn = conn_cls(parsed.hostname, port, timeout=timeout or cfg.REQUEST_TIMEOUT_SECONDS)
	start = time.perf_counter()
	conn.request(method, path, headers=headers)
	resp = conn.getresponse()
	first_byte_ms = (time.perf_counter() - start) * 1000.0
	body = resp.read()
	elapsed_ms = (time.perf_counter() - start) * 1000.0
	final_url = url  # naive; without redirects handling via low-level HTTP
	return HttpResponse(status=resp.status, headers=normalize_headers(resp.getheaders()), body=body, elapsed_ms=elapsed_ms, final_url=final_url)


def extract_links(html: bytes, base_url: str) -> List[str]:
	# Very basic href/src extraction; avoids heavy dependencies
	text = html.decode("utf-8", errors="ignore")
	urls: List[str] = []
	for pattern in (r"href\s*=\s*\"([^\"]+)\"", r"href\s*=\s*'([^']+)'", r"src\s*=\s*\"([^\"]+)\"", r"src\s*=\s*'([^']+)'"):
		for match in re.findall(pattern, text, flags=re.IGNORECASE):
			urls.append(urllib.parse.urljoin(base_url, match))
	return urls


def is_allowed_url(url: str) -> bool:
	parsed = urllib.parse.urlparse(url)
	return (parsed.scheme in ("http", "https")) and (parsed.hostname in cfg.ALLOWED_HOSTS)


def check_ssl_expiry(hostname: str) -> Tuple[Optional[int], Optional[str]]:
	# Returns (days_left, error)
	import socket
	try:
		with socket.create_connection((hostname, 443), timeout=cfg.REQUEST_TIMEOUT_SECONDS) as sock:
			with ssl_module.create_default_context().wrap_socket(sock, server_hostname=hostname) as ssock:
				cert = ssock.getpeercert()
			expires_str = cert.get("notAfter")
			if not expires_str:
				return None, "No notAfter in certificate"
			# Format like 'Jun 20 12:00:00 2026 GMT'
			expires = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z")
			days = (expires - datetime.utcnow()).days
			return days, None
	except Exception as e:
		return None, str(e)


def now_iso() -> str:
	return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


