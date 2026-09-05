from __future__ import annotations

import difflib
import ipaddress
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

DEFAULT_ENDPOINT = "http://127.0.0.1:8081/v2/check"
PUBLIC_FREE_HOST = "api.languagetool.org"


class LanguageToolError(RuntimeError):
    pass


@dataclass(slots=True)
class LanguageToolSettings:
    enabled: bool
    endpoint: str
    language: str
    timeout_seconds: int


@dataclass(slots=True)
class ProofreadingIssue:
    message: str
    short_message: str
    offset: int
    length: int
    replacements: tuple[str, ...]
    rule_id: str
    category: str
    issue_type: str
    context: str


@dataclass(slots=True)
class ProofreadingResult:
    issues: tuple[ProofreadingIssue, ...]
    language: str
    software_version: str
    incomplete_results: bool


def load_languagetool_settings(config: dict[str, Any]) -> LanguageToolSettings:
    proofreading = config.get("proofreading", {})
    return LanguageToolSettings(
        enabled=bool(proofreading.get("enabled", False)),
        endpoint=str(proofreading.get("endpoint", DEFAULT_ENDPOINT)).strip(),
        language=str(proofreading.get("language", "en-US")).strip(),
        timeout_seconds=int(proofreading.get("timeout_seconds", 30)),
    )


def requires_data_transfer_consent(settings: LanguageToolSettings) -> bool:
    return not _validate_endpoint(settings.endpoint)


def check_text(
    text: str,
    settings: LanguageToolSettings,
    *,
    language: str | None = None,
    allow_data_transfer: bool = False,
) -> ProofreadingResult:
    if not settings.enabled:
        raise LanguageToolError(
            "LanguageTool proofreading is disabled in .openscribe/project.yaml. Set proofreading.enabled to true first."
        )

    is_local = _validate_endpoint(settings.endpoint)
    if not is_local and not allow_data_transfer:
        raise LanguageToolError(
            "This command sends the complete chapter text to the configured hosted "
            "LanguageTool endpoint. Review that service's data policy, then rerun with "
            "--allow-data-transfer if you approve this transfer."
        )

    selected_language = (language or settings.language).strip()
    if not selected_language:
        raise LanguageToolError("LanguageTool language cannot be empty.")

    body = urlencode({"text": text, "language": selected_language}).encode("utf-8")
    request = Request(
        settings.endpoint,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "OpenScribe/0.1.0",
        },
        method="POST",
    )

    try:
        # _validate_endpoint restricts the URL to HTTP or HTTPS before this call.
        with urlopen(request, timeout=settings.timeout_seconds) as response:  # nosec B310
            response_body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise LanguageToolError(f"LanguageTool returned HTTP {exc.code} {exc.reason}.") from exc
    except URLError as exc:
        raise LanguageToolError(f"Could not connect to LanguageTool: {exc.reason}") from exc
    except TimeoutError as exc:
        raise LanguageToolError(f"LanguageTool did not respond within {settings.timeout_seconds} seconds.") from exc

    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise LanguageToolError("LanguageTool returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise LanguageToolError("LanguageTool returned an invalid response object.")
    matches = payload.get("matches", [])
    if not isinstance(matches, list):
        raise LanguageToolError("LanguageTool response field 'matches' must be a list.")

    language_data = payload.get("language", {})
    software_data = payload.get("software", {})
    warnings_data = payload.get("warnings", {})
    return ProofreadingResult(
        issues=tuple(_normalize_issue(text, _parse_issue(item)) for item in matches),
        language=str(language_data.get("code", selected_language))
        if isinstance(language_data, dict)
        else selected_language,
        software_version=str(software_data.get("version", "unknown")) if isinstance(software_data, dict) else "unknown",
        incomplete_results=bool(warnings_data.get("incompleteResults", False))
        if isinstance(warnings_data, dict)
        else False,
    )


def line_and_column(text: str, offset: int) -> tuple[int, int]:
    bounded_offset = min(max(offset, 0), len(text))
    prefix = text[:bounded_offset]
    return prefix.count("\n") + 1, len(prefix.rsplit("\n", 1)[-1]) + 1


def _normalize_issue(text: str, issue: ProofreadingIssue) -> ProofreadingIssue:
    boundaries = {0: 0}
    units = 0
    for index, character in enumerate(text):
        units += 2 if ord(character) > 0xFFFF else 1
        boundaries[units] = index + 1
    end = issue.offset + issue.length
    if issue.offset not in boundaries or end not in boundaries:
        raise LanguageToolError("LanguageTool returned an invalid UTF-16 text range.")
    start = boundaries[issue.offset]
    issue.length = boundaries[end] - start
    issue.offset = start
    return issue


@dataclass(frozen=True, slots=True)
class ReplacementPreview:
    before: str
    after: str
    offset: int
    length: int
    replacement: str

    @property
    def diff(self) -> str:
        return "\n".join(difflib.unified_diff(
            self.before.splitlines(), self.after.splitlines(), fromfile="before", tofile="suggestion", lineterm=""
        ))

    def apply(self, current: str) -> str:
        if current != self.before:
            raise LanguageToolError("Text changed after proofreading. Run the check again before applying a suggestion.")
        return self.after


def preview_replacement(text: str, issue: ProofreadingIssue, replacement: str) -> ReplacementPreview:
    if replacement not in issue.replacements:
        raise LanguageToolError("Choose one of this finding's replacement suggestions.")
    if issue.offset < 0 or issue.length < 0 or issue.offset + issue.length > len(text):
        raise LanguageToolError("The finding points outside the checked text.")
    return ReplacementPreview(
        text, text[:issue.offset] + replacement + text[issue.offset + issue.length:],
        issue.offset, issue.length, replacement,
    )


def _validate_endpoint(endpoint: str) -> bool:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise LanguageToolError("LanguageTool endpoint must be an absolute HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise LanguageToolError("LanguageTool credentials cannot be embedded in the endpoint URL.")
    if parsed.query or parsed.fragment:
        raise LanguageToolError("LanguageTool endpoint cannot contain a query string or fragment.")
    if not parsed.path.rstrip("/").endswith("/v2/check"):
        raise LanguageToolError("LanguageTool endpoint must end with /v2/check.")

    hostname = parsed.hostname.lower()
    if hostname == PUBLIC_FREE_HOST:
        raise LanguageToolError(
            "The free public LanguageTool endpoint does not permit automated requests. "
            "Use a local server or a licensed hosted endpoint."
        )

    is_local = hostname == "localhost"
    if not is_local:
        try:
            is_local = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            is_local = False
    if not is_local and parsed.scheme != "https":
        raise LanguageToolError("Hosted LanguageTool endpoints must use HTTPS.")
    return is_local


def _parse_issue(value: Any) -> ProofreadingIssue:
    if not isinstance(value, dict):
        raise LanguageToolError("LanguageTool returned an invalid match entry.")
    rule = value.get("rule", {})
    category = rule.get("category", {}) if isinstance(rule, dict) else {}
    replacements = value.get("replacements", [])
    if not isinstance(replacements, list):
        replacements = []
    context = value.get("context", {})
    return ProofreadingIssue(
        message=str(value.get("message", "LanguageTool finding")),
        short_message=str(value.get("shortMessage", "")),
        offset=_integer(value.get("offset", 0), "offset"),
        length=_integer(value.get("length", 0), "length"),
        replacements=tuple(
            str(replacement.get("value", ""))
            for replacement in replacements
            if isinstance(replacement, dict) and replacement.get("value") is not None
        ),
        rule_id=str(rule.get("id", "unknown")) if isinstance(rule, dict) else "unknown",
        category=str(category.get("name", "Uncategorized")) if isinstance(category, dict) else "Uncategorized",
        issue_type=str(rule.get("issueType", "unknown")) if isinstance(rule, dict) else "unknown",
        context=str(context.get("text", "")) if isinstance(context, dict) else "",
    )


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LanguageToolError(f"LanguageTool match field '{field}' must be an integer.")
    return value
