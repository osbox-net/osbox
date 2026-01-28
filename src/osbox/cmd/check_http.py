from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse

import requests


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    message: str


def normalize_url(raw: str, default_scheme: str, default_path: str) -> str:
    """
    Accepts:
      - localhost:5000
      - localhost:5000/healthz
      - http://localhost:5000
      - https://keystone:5000/v3
    Returns a full URL with scheme + path.
    """
    raw = raw.strip()

    if "://" not in raw:
        raw = f"{default_scheme}://{raw}"

    u = urlparse(raw)

    if not u.hostname:
        raise ValueError("Missing hostname in target")

    # Default port if not provided
    netloc = u.netloc
    if u.port is None:
        default_port = 443 if u.scheme == "https" else 80
        host = u.hostname
        netloc = f"{host}:{default_port}"

    # Default path if missing
    path = u.path or default_path
    if not path.startswith("/"):
        path = "/" + path

    return urlunparse((u.scheme, netloc, path, "", u.query, ""))


def parse_status_list(s: str) -> set[int]:
    """
    Supports:
      "200" or "200,204" or "200-299,301,302"
    """
    out: set[int] = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a_s, b_s = part.split("-", 1)
            a, b = int(a_s), int(b_s)
            if a > b:
                a, b = b, a
            out.update(range(a, b + 1))
        else:
            out.add(int(part))
    return out


def parse_headers(header_args: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for h in header_args:
        if ":" not in h:
            raise ValueError(f"Invalid header (expected 'Key: Value'): {h!r}")
        k, v = h.split(":", 1)
        headers[k.strip()] = v.strip()
    return headers


def check_http(
    *,
    target: str,
    default_scheme: str = "http",
    default_path: str = "/",
    method: str = "GET",
    timeout: float = 2.0,
    retries: int = 0,
    ok_statuses: str = "200-399",
    insecure: bool = False,
    headers: Optional[dict[str, str]] = None,
) -> CheckResult:
    """
    Performs the HTTP check. Returns (ok, message).
    Message is suitable for stderr on failure, or stdout on success (if you want).
    """
    url = normalize_url(target, default_scheme, default_path)
    ok_set = parse_status_list(ok_statuses)
    
    hdrs = {
        "User-Agent": "osbox-check-http/1.0",
        **(headers or {}),
    }

    session = requests.Session()
    last_exc: Optional[Exception] = None

    for _attempt in range(retries + 1):
        try:
            resp = session.request(
                method=method,
                url=url,
                headers=hdrs,
                timeout=timeout,
                allow_redirects=False,
                verify=not insecure,
            )
            status = resp.status_code

            if status in ok_set:
                return CheckResult(True, f"healthy: HTTP {status} {url}")

            return CheckResult(False, f"unhealthy: HTTP {status} (ok: {ok_statuses}) {url}")

        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc = e
            continue

    return CheckResult(False, f"unhealthy: {type(last_exc).__name__ if last_exc else 'error'} {last_exc} {url}")


def _isatty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def main() -> None:
    p = argparse.ArgumentParser(prog="osbox check-http")
    p.add_argument("target", help="host:port[/path] or http(s)://host:port/path")
    p.add_argument(
        "--scheme",
        choices=["http", "https"],
        default="http",
        help="Default scheme for bare host:port (default: http)",
    )
    p.add_argument("--path", default="/", help="Default path for bare host:port (default: /)")
    p.add_argument("--method", choices=["GET", "HEAD"], default="GET", help="HTTP method (default: GET)")
    p.add_argument("--timeout", type=float, default=2.0, help="Timeout seconds (default: 2)")
    p.add_argument("--retries", type=int, default=0, help="Retry count on network errors (default: 0)")
    p.add_argument("--ok", default="200-399", help="OK status codes, e.g. 200-299,301,302 (default: 200-399)")
    p.add_argument("--insecure", action="store_true", help="Skip TLS verification for https")
    p.add_argument("--header", action="append", default=[], help='Extra header, repeatable: --header "X-Foo: bar"')
    p.add_argument("--quiet", action="store_true", help="No output; just exit code")
    args = p.parse_args()

    try:
        headers = parse_headers(args.header)

        res = check_http(
            target=args.target,
            default_scheme=args.scheme,
            default_path=args.path,
            method=args.method,
            timeout=args.timeout,
            retries=args.retries,
            ok_statuses=args.ok,
            insecure=args.insecure,
            headers=headers,
        )

        if res.ok:
            if not args.quiet and _isatty():
                print(res.message)
            sys.exit(0)

        if not args.quiet:
            print(res.message, file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        if not getattr(args, "quiet", False):
            print(f"unhealthy: {e}", file=sys.stderr)
        sys.exit(1)
