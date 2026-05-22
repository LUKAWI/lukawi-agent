from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx

from lukawi.tools.base import (
    ToolDefinition,
    ToolResult,
    ToolParameter,
    ToolParameterType,
)
from lukawi.tools.registry import ToolRegistry


ALLOWED_SCHEMES = ("http", "https")
MAX_REDIRECTS = 20
DEFAULT_MAX_RESPONSE_SIZE = 5 * 1024 * 1024


WEB_FETCH_TOOL = ToolDefinition(
    name="web_fetch",
    description="Fetch content from a URL. Returns markdown, text, or HTML.",
    parameters=[
        ToolParameter(
            name="url",
            type=ToolParameterType.STRING,
            description="URL to fetch",
        ),
        ToolParameter(
            name="format",
            type=ToolParameterType.STRING,
            description="Output format: markdown, text, html",
            required=False,
            default="markdown",
            enum=["markdown", "text", "html"],
        ),
        ToolParameter(
            name="timeout",
            type=ToolParameterType.NUMBER,
            description="Request timeout in seconds",
            required=False,
            default=30,
        ),
        ToolParameter(
            name="follow_redirects",
            type=ToolParameterType.BOOLEAN,
            description="Whether to follow redirects",
            required=False,
            default=True,
        ),
        ToolParameter(
            name="max_response_size",
            type=ToolParameterType.INTEGER,
            description="Maximum response body size in bytes",
            required=False,
            default=DEFAULT_MAX_RESPONSE_SIZE,
        ),
    ],
    category="web",
    tags=["http", "fetch", "web", "url"],
)


def is_internal_ip(host: str) -> bool:
    host = host.strip().lower()

    if host in ("localhost", "localhost.localdomain"):
        return True

    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]

    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        try:
            addrs = socket.getaddrinfo(host, 80)
            for family, _, _, _, sockaddr in addrs:
                ip = sockaddr[0]
                if is_internal_ip(ip):
                    return True
            return False
        except socket.gaierror:
            return False

    if addr.is_loopback:
        return True
    if addr.is_private:
        return True
    if addr.is_link_local:
        return True
    if addr.is_unspecified:
        return True

    return False


def _validate_url(url: str) -> str | None:
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        return f"URL scheme '{parsed.scheme}' is not allowed. Only http:// and https:// are permitted."

    host = parsed.hostname
    if host is None:
        return f"URL '{url}' has no valid hostname."

    if is_internal_ip(host):
        return f"URL '{url}' resolves to an internal or reserved address."

    return None


async def web_fetch_handler(
    url: str,
    format: str = "markdown",
    timeout: float = 30,
    follow_redirects: bool = True,
    max_response_size: int = DEFAULT_MAX_RESPONSE_SIZE,
) -> ToolResult:
    error = _validate_url(url)
    if error:
        return ToolResult.error(f"SSRF protection: {error}")

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=timeout,
        ) as client:
            current_url = url
            response = await client.get(current_url)

            redirect_count = 0
            while response.is_redirect and follow_redirects and redirect_count < MAX_REDIRECTS:
                redirect_count += 1
                location = response.headers.get("location")
                if not location:
                    break

                current_url = urljoin(str(response.url), location)

                error = _validate_url(current_url)
                if error:
                    return ToolResult.error(f"SSRF protection: Redirect target {error}")

                response = await client.get(current_url)

            response.raise_for_status()

            content_bytes = response.content
            if len(content_bytes) > max_response_size:
                return ToolResult.error(
                    f"Response too large (exceeded {max_response_size} bytes)"
                )

            content = content_bytes.decode("utf-8", errors="replace")

            content_type = response.headers.get("content-type", "")

            if format == "text" and "html" in content_type:
                content = _html_to_text(content)
            elif format == "markdown" and "html" in content_type:
                content = _html_to_markdown(content)

            return ToolResult.success(
                result=content,
                metadata={
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "url": str(response.url),
                },
            )

    except httpx.TimeoutException:
        return ToolResult.timeout(f"Request to {url} timed out after {timeout}s")

    except httpx.HTTPStatusError as e:
        return ToolResult.error(
            f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
        )

    except Exception as e:
        return ToolResult.error(f"Failed to fetch {url}: {str(e)}")


def _html_to_text(html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _html_to_markdown(html: str) -> str:
    md = html

    md = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", md, flags=re.DOTALL | re.IGNORECASE)

    md = re.sub(r"<b>(.*?)</b>", r"**\1**", md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r"<strong>(.*?)</strong>", r"**\1**", md, flags=re.DOTALL | re.IGNORECASE)

    md = re.sub(r"<i>(.*?)</i>", r"*\1*", md, flags=re.DOTALL | re.IGNORECASE)
    md = re.sub(r"<em>(.*?)</em>", r"*\1*", md, flags=re.DOTALL | re.IGNORECASE)

    md = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r"[\2](\1)",
        md,
        flags=re.DOTALL | re.IGNORECASE,
    )

    md = re.sub(r"<br\s*/?>", "\n", md, flags=re.IGNORECASE)
    md = re.sub(r"<p[^>]*>", "", md, flags=re.IGNORECASE)
    md = re.sub(r"</p>", "\n\n", md, flags=re.IGNORECASE)

    md = re.sub(r"<[^>]+>", "", md)

    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+", " ", md)

    return md.strip()


def register_web_fetch(registry: ToolRegistry) -> None:
    registry.register(WEB_FETCH_TOOL, web_fetch_handler)
