"""SSDP-based discovery of Bambu Lab printers on the local network."""

from __future__ import annotations

import select
import socket
import time
from urllib.parse import urlparse

_SSDP_ADDR = "239.255.255.250"
_SSDP_PORT = 1900
_BAMBU_ST = "urn:bambulab-com:device:3dprinter:1"

_MSEARCH = (
    "M-SEARCH * HTTP/1.1\r\n"
    f"HOST: {_SSDP_ADDR}:{_SSDP_PORT}\r\n"
    'MAN: "ssdp:discover"\r\n'
    f"ST: {_BAMBU_ST}\r\n"
    "MX: 2\r\n"
    "\r\n"
).encode("ascii")

_MOCK_PRINTERS: list[dict[str, str]] = [
    {
        "ip": "192.168.1.100",
        "serial": "MOCK_SERIAL_001",
        "model": "H2C",
        "name": "BambuLab H2C",
        "firmware": "01.08.00.00",
        "signal": "-42dBm",
    }
]


def _parse_header_block(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw.split("\r\n"):
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        headers[key.strip().lower()] = value.strip()
    return headers


def _location_to_ip(location: str) -> str | None:
    location = location.strip()
    if not location:
        return None
    if location.startswith("http://") or location.startswith("https://"):
        parsed = urlparse(location)
        host = parsed.hostname
        return host if host else None
    host_part = location.split("/")[0]
    if ":" in host_part and not host_part.startswith("["):
        host_part = host_part.rsplit(":", 1)[0]
    try:
        socket.inet_aton(host_part)
        return host_part
    except OSError:
        return None


def _normalize_signal(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if "dbm" in raw.lower():
        return raw
    return f"{raw}dBm" if raw.lstrip("-").isdigit() or raw.startswith("-") else raw


def _parse_bambu_ssdp(text: str, peer_ip: str) -> dict[str, str] | None:
    if "\r\n\r\n" in text:
        text = text.split("\r\n\r\n", 1)[0]
    first_line, _, rest = text.partition("\r\n")
    if not first_line.startswith("HTTP/"):
        return None
    headers = _parse_header_block(rest)
    if "devmodel.bambu.com" not in headers:
        return None

    location = headers.get("location", "")
    ip = _location_to_ip(location) or peer_ip
    serial = headers.get("usn", "").strip()
    model = headers.get("devmodel.bambu.com", "").strip()
    name = headers.get("devname.bambu.com", "").strip()
    firmware = (
        headers.get("devversion.bambu.com", "")
        or headers.get("devfirmware.bambu.com", "")
        or headers.get("firmwareversion", "")
    ).strip()
    signal_raw = headers.get("devsignal.bambu.com", "").strip()
    signal = _normalize_signal(signal_raw) if signal_raw else ""

    return {
        "ip": ip,
        "serial": serial,
        "model": model,
        "name": name,
        "firmware": firmware,
        "signal": signal,
    }


def discover_printers(mock: bool = False, timeout: float = 5) -> list[dict[str, str]]:
    """Discover Bambu printers via SSDP (or return mock data when ``mock`` is True)."""
    if mock:
        return list(_MOCK_PRINTERS)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    except OSError:
        pass
    sock.bind(("", 0))
    sock.setblocking(False)

    sock.sendto(_MSEARCH, (_SSDP_ADDR, _SSDP_PORT))

    found: dict[tuple[str, str], dict[str, str]] = {}
    buf_size = 8192
    end = time.monotonic() + timeout

    try:
        while time.monotonic() < end:
            remaining = end - time.monotonic()
            if remaining <= 0:
                break
            readable, _, _ = select.select([sock], [], [], min(remaining, 1.0))
            if not readable:
                continue
            try:
                data, addr = sock.recvfrom(buf_size)
            except BlockingIOError:
                continue
            peer_ip = addr[0]
            try:
                text = data.decode("utf-8", errors="replace")
            except Exception:
                continue
            parsed = _parse_bambu_ssdp(text, peer_ip)
            if parsed is None:
                continue
            key = (parsed["ip"], parsed["serial"] or parsed["model"] or peer_ip)
            if key not in found:
                found[key] = parsed
    finally:
        sock.close()

    return list(found.values())
