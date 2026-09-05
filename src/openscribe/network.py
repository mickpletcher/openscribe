from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def local_endpoint(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Provider endpoint must be an absolute HTTP or HTTPS URL.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Provider endpoints cannot include credentials, a query, or a fragment.")
    try:
        port = parsed.port
        if port is not None and port == 0:
            raise ValueError("Port zero cannot be used as a provider destination.")
    except ValueError as exc:
        raise ValueError("Provider endpoint has an invalid port.") from exc
    hostname = parsed.hostname.lower()
    try:
        local = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        local = hostname == "localhost"
    if not local and parsed.scheme != "https":
        raise ValueError("Nonlocal provider endpoints must use HTTPS.")
    return local
