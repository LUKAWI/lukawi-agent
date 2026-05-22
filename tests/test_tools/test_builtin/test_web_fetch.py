import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from lukawi.tools.builtin.web_fetch import (
    web_fetch_handler,
    WEB_FETCH_TOOL,
    register_web_fetch,
    _html_to_text,
    _html_to_markdown,
    is_internal_ip,
    _validate_url,
)
from lukawi.tools.base import ToolResultStatus
from lukawi.tools.registry import ToolRegistry


def _make_mock_response(
    text: str = "<html></html>",
    url: str = "https://example.com",
    status_code: int = 200,
    content_type: str = "text/html",
    is_redirect: bool = False,
):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text
    mock_response.url = url
    mock_response.headers = {"content-type": content_type}
    mock_response.is_redirect = is_redirect
    mock_response.raise_for_status = MagicMock()
    mock_response.content = text.encode("utf-8")
    return mock_response


class TestWebFetchDefinition:

    def test_tool_name(self):
        assert WEB_FETCH_TOOL.name == "web_fetch"

    def test_tool_category(self):
        assert WEB_FETCH_TOOL.category == "web"

    def test_has_description(self):
        assert len(WEB_FETCH_TOOL.description) > 0

    def test_has_url_parameter(self):
        url_param = next(p for p in WEB_FETCH_TOOL.parameters if p.name == "url")
        assert url_param.required is True

    def test_format_parameter_defaults_to_markdown(self):
        fmt = next(p for p in WEB_FETCH_TOOL.parameters if p.name == "format")
        assert fmt.required is False
        assert fmt.default == "markdown"

    def test_format_parameter_enum(self):
        fmt = next(p for p in WEB_FETCH_TOOL.parameters if p.name == "format")
        assert fmt.enum is not None
        assert set(fmt.enum) == {"markdown", "text", "html"}

    def test_timeout_parameter(self):
        timeout = next(p for p in WEB_FETCH_TOOL.parameters if p.name == "timeout")
        assert timeout.required is False
        assert timeout.default == 30

    def test_follow_redirects_parameter(self):
        fr = next(p for p in WEB_FETCH_TOOL.parameters if p.name == "follow_redirects")
        assert fr.required is False
        assert fr.default is True

    def test_max_response_size_parameter(self):
        mrs = next(
            p for p in WEB_FETCH_TOOL.parameters if p.name == "max_response_size"
        )
        assert mrs.required is False
        assert mrs.default == 5 * 1024 * 1024

    def test_has_tags(self):
        assert "http" in WEB_FETCH_TOOL.tags
        assert "web" in WEB_FETCH_TOOL.tags

    def test_to_openai_schema(self):
        schema = WEB_FETCH_TOOL.to_openai_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_fetch"
        assert "url" in schema["function"]["parameters"]["properties"]


class TestWebFetchHandlerSuccess:

    @pytest.mark.asyncio
    async def test_fetch_returns_success(self):
        mock_response = _make_mock_response(
            text="<html><body>Hello</body></html>"
        )

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = mock_response

            result = await web_fetch_handler("https://example.com")

            assert result.status == ToolResultStatus.SUCCESS
            assert "Hello" in result.result

    @pytest.mark.asyncio
    async def test_fetch_includes_metadata(self):
        mock_response = _make_mock_response(
            text="<html>OK</html>",
            url="https://example.com/page",
            content_type="text/html; charset=utf-8",
        )

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = mock_response

            result = await web_fetch_handler("https://example.com")

            assert result.metadata["status_code"] == 200
            assert "text/html" in result.metadata["content_type"]
            assert result.metadata["url"] == "https://example.com/page"

    @pytest.mark.asyncio
    async def test_fetch_text_format_strips_tags(self):
        mock_response = _make_mock_response(
            text="<p>Hello <b>world</b></p>"
        )

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = mock_response

            result = await web_fetch_handler("https://example.com", format="text")

            assert result.status == ToolResultStatus.SUCCESS
            assert "Hello world" in result.result
            assert "<p>" not in result.result

    @pytest.mark.asyncio
    async def test_fetch_markdown_format_converts_headers(self):
        mock_response = _make_mock_response(
            text="<h1>Title</h1><p>Content</p>"
        )

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = mock_response

            result = await web_fetch_handler("https://example.com", format="markdown")

            assert result.status == ToolResultStatus.SUCCESS
            assert "# Title" in result.result

    @pytest.mark.asyncio
    async def test_fetch_html_format_preserves_markup(self):
        mock_response = _make_mock_response(text="<p>Hello</p>")

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = mock_response

            result = await web_fetch_handler("https://example.com", format="html")

            assert result.status == ToolResultStatus.SUCCESS
            assert "<p>" in result.result


class TestWebFetchHandlerErrors:

    @pytest.mark.asyncio
    async def test_fetch_timeout(self):
        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.side_effect = httpx.TimeoutException("timeout")

            result = await web_fetch_handler("https://example.com", timeout=0.1)

            assert result.status == ToolResultStatus.TIMEOUT
            assert result.error_message is not None
            assert "timed out" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_http_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.side_effect = httpx.HTTPStatusError(
                "404", request=MagicMock(), response=mock_response
            )

            result = await web_fetch_handler("https://example.com/missing")

            assert result.status == ToolResultStatus.ERROR
            assert "404" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_http_500(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=mock_response
            )

            result = await web_fetch_handler("https://example.com")

            assert result.status == ToolResultStatus.ERROR
            assert "500" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_connection_error(self):
        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            result = await web_fetch_handler("https://invalid.example.com")

            assert result.status == ToolResultStatus.ERROR
            assert "Failed to fetch" in result.error_message


class TestHtmlToText:

    def test_strips_paragraph_tags(self):
        assert "Hello world" in _html_to_text("<p>Hello <b>world</b></p>")

    def test_removes_script_elements(self):
        html = '<p>Text</p><script>alert("xss")</script>'
        text = _html_to_text(html)
        assert "Text" in text
        assert "alert" not in text

    def test_removes_style_elements(self):
        html = "<p>Text</p><style>.cls{color:red}</style>"
        text = _html_to_text(html)
        assert "Text" in text
        assert "color" not in text

    def test_collapses_whitespace(self):
        html = "<p>  Hello   world  </p>"
        text = _html_to_text(html)
        assert "  " not in text.strip()

    def test_empty_input(self):
        assert _html_to_text("") == ""


class TestHtmlToMarkdown:

    def test_h1_to_markdown(self):
        assert "# Title" in _html_to_markdown("<h1>Title</h1>")

    def test_h2_to_markdown(self):
        assert "## Sub" in _html_to_markdown("<h2>Sub</h2>")

    def test_h3_to_markdown(self):
        assert "### Sub" in _html_to_markdown("<h3>Sub</h3>")

    def test_bold_strong(self):
        md = _html_to_markdown("<strong>bold</strong>")
        assert "**bold**" in md

    def test_bold_b_tag(self):
        md = _html_to_markdown("<b>bold</b>")
        assert "**bold**" in md

    def test_italic_em(self):
        md = _html_to_markdown("<em>italic</em>")
        assert "*italic*" in md

    def test_link_conversion(self):
        md = _html_to_markdown('<a href="https://example.com">click</a>')
        assert "[click](https://example.com)" in md

    def test_paragraph_to_double_newline(self):
        md = _html_to_markdown("<p>First</p><p>Second</p>")
        assert "First\n\nSecond" in md

    def test_br_to_newline(self):
        md = _html_to_markdown("Line1<br>Line2")
        assert "\n" in md

    def test_removes_remaining_tags(self):
        md = _html_to_markdown("<div>content</div>")
        assert "<div>" not in md
        assert "content" in md

    def test_collapses_excessive_newlines(self):
        md = _html_to_markdown("<p>a</p><p>b</p><p>c</p>")
        assert "\n\n\n" not in md


class TestRegisterWebFetch:

    def test_register_adds_to_registry(self):
        registry = ToolRegistry()
        register_web_fetch(registry)
        assert registry.has("web_fetch")

    def test_registered_handler_is_callable(self):
        registry = ToolRegistry()
        register_web_fetch(registry)
        _, handler = registry.get("web_fetch")
        assert callable(handler)

    def test_registered_definition_matches(self):
        registry = ToolRegistry()
        register_web_fetch(registry)
        defn, _ = registry.get("web_fetch")
        assert defn.name == "web_fetch"
        assert defn.category == "web"


class TestIsInternalIp:

    def test_ipv4_loopback(self):
        assert is_internal_ip("127.0.0.1") is True

    def test_ipv6_loopback(self):
        assert is_internal_ip("::1") is True

    def test_ipv6_loopback_brackets(self):
        assert is_internal_ip("[::1]") is True

    def test_unspecified_ipv4(self):
        assert is_internal_ip("0.0.0.0") is True

    def test_private_10_dot(self):
        assert is_internal_ip("10.0.0.1") is True
        assert is_internal_ip("10.255.255.255") is True

    def test_private_172_dot(self):
        assert is_internal_ip("172.16.0.1") is True
        assert is_internal_ip("172.31.255.255") is True

    def test_private_192_dot(self):
        assert is_internal_ip("192.168.0.1") is True
        assert is_internal_ip("192.168.255.255") is True

    def test_link_local(self):
        assert is_internal_ip("169.254.0.1") is True
        assert is_internal_ip("169.254.169.254") is True

    def test_public_ip(self):
        assert is_internal_ip("8.8.8.8") is False
        assert is_internal_ip("93.184.216.34") is False

    def test_public_ip_172_dot(self):
        assert is_internal_ip("172.32.0.1") is False

    def test_localhost_domain(self):
        assert is_internal_ip("localhost") is True

    def test_ipv6_unspecified(self):
        assert is_internal_ip("::") is True
        assert is_internal_ip("[::]") is True


class TestValidateUrl:

    def test_allowed_https(self):
        assert _validate_url("https://example.com") is None

    def test_allowed_http(self):
        assert _validate_url("http://example.com") is None

    def test_rejects_file_scheme(self):
        error = _validate_url("file:///etc/passwd")
        assert error is not None
        assert "scheme" in error

    def test_rejects_ftp_scheme(self):
        error = _validate_url("ftp://example.com/file")
        assert error is not None
        assert "scheme" in error

    def test_rejects_localhost_url(self):
        error = _validate_url("http://localhost:8080/admin")
        assert error is not None
        assert "internal" in error or "SSRF" in _validate_url.__name__

    def test_rejects_localhost_ip(self):
        error = _validate_url("http://127.0.0.1:8080/")
        assert error is not None
        assert "internal" in error

    def test_rejects_private_ip(self):
        error = _validate_url("http://192.168.1.1/")
        assert error is not None
        assert "internal" in error

    def test_rejects_metadata_service(self):
        error = _validate_url("http://169.254.169.254/")
        assert error is not None
        assert "internal" in error

    def test_rejects_empty_url(self):
        error = _validate_url("")
        assert error is not None

    def test_rejects_url_without_hostname(self):
        error = _validate_url("http://")
        assert error is not None
        assert "hostname" in error


class TestWebFetchHandlerSSRF:

    @pytest.mark.asyncio
    async def test_rejects_internal_ip(self):
        result = await web_fetch_handler("http://127.0.0.1:8080/")
        assert result.status == ToolResultStatus.ERROR
        assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_rejects_localhost(self):
        result = await web_fetch_handler("http://localhost:8080/")
        assert result.status == ToolResultStatus.ERROR
        assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_rejects_private_network(self):
        result = await web_fetch_handler("http://192.168.1.1/admin")
        assert result.status == ToolResultStatus.ERROR
        assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_rejects_metadata_service(self):
        result = await web_fetch_handler("http://169.254.169.254/")
        assert result.status == ToolResultStatus.ERROR
        assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_rejects_file_scheme(self):
        result = await web_fetch_handler("file:///etc/passwd")
        assert result.status == ToolResultStatus.ERROR
        assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_rejects_ftp_scheme(self):
        result = await web_fetch_handler("ftp://example.com/file")
        assert result.status == ToolResultStatus.ERROR
        assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_rejects_redirect_to_internal(self):
        mock_initial = MagicMock()
        mock_initial.status_code = 302
        mock_initial.is_redirect = True
        mock_initial.headers = {"location": "http://192.168.1.1/admin"}
        mock_initial.url = "https://public.example.com/redirect"
        mock_initial.raise_for_status = MagicMock()
        mock_initial.content = b""

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_initial

            result = await web_fetch_handler("https://public.example.com/redirect")

            assert result.status == ToolResultStatus.ERROR
            assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_rejects_redirect_to_localhost(self):
        mock_initial = MagicMock()
        mock_initial.status_code = 301
        mock_initial.is_redirect = True
        mock_initial.headers = {"location": "http://localhost:9000/"}
        mock_initial.url = "https://public.example.com/redirect"
        mock_initial.raise_for_status = MagicMock()
        mock_initial.content = b""

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_initial

            result = await web_fetch_handler("https://public.example.com/redirect")

            assert result.status == ToolResultStatus.ERROR
            assert "SSRF" in result.error_message

    @pytest.mark.asyncio
    async def test_allows_public_redirect(self):
        mock_initial = MagicMock()
        mock_initial.status_code = 302
        mock_initial.is_redirect = True
        mock_initial.headers = {"location": "https://other-public.com/page"}
        mock_initial.url = "https://public.example.com/redirect"
        mock_initial.raise_for_status = MagicMock()
        mock_initial.content = b""

        mock_final = _make_mock_response(
            text="redirected content",
            url="https://other-public.com/page",
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_initial, mock_final]

            result = await web_fetch_handler("https://public.example.com/redirect")

            assert result.status == ToolResultStatus.SUCCESS
            assert "redirected content" in result.result

    @pytest.mark.asyncio
    async def test_max_response_size_enforced(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_redirect = False
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"a" * 100

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = mock_response

            result = await web_fetch_handler(
                "https://example.com", max_response_size=50
            )

            assert result.status == ToolResultStatus.ERROR
            assert "too large" in result.error_message

    @pytest.mark.asyncio
    async def test_max_response_size_allows_under_limit(self):
        mock_response = _make_mock_response(text="small content")

        with (
            patch("lukawi.tools.builtin.web_fetch._validate_url", return_value=None),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        ):
            mock_get.return_value = mock_response

            result = await web_fetch_handler(
                "https://example.com", max_response_size=1000
            )

            assert result.status == ToolResultStatus.SUCCESS
            assert "small content" in result.result

    @pytest.mark.asyncio
    async def test_rejects_unspecified_address(self):
        result = await web_fetch_handler("http://0.0.0.0:8080/")
        assert result.status == ToolResultStatus.ERROR
        assert "SSRF" in result.error_message
