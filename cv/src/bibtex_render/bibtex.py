"""Minimal BibTeX parser for publication rendering use-cases."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True)
class BibEntry:
    entry_type: str
    key: str
    fields: dict[str, str]


@dataclass(slots=True)
class BibParseIssue:
    line: int
    entry_type: str
    key: str
    message: str


@dataclass(slots=True)
class BibParseResult:
    entries: list[BibEntry]
    issues: list[BibParseIssue]


_ENTRY_HEADER = re.compile(
    r"(?m)^[ \t]*@(?P<etype>[A-Za-z][A-Za-z0-9_-]*)[ \t]*[({][ \t]*(?P<key>[^,\s{}()]+)?"
)
_FIELD_SEPARATOR_IN_VALUE = re.compile(r",\s*[A-Za-z][A-Za-z0-9_-]*\s*=")


class _BibParser:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.size = len(text)
        self.issues: list[BibParseIssue] = []
        self._current_entry_type = ""
        self._current_entry_key = ""
        self._current_entry_line = 1
        self.macros = {
            "jan": "January",
            "feb": "February",
            "mar": "March",
            "apr": "April",
            "may": "May",
            "jun": "June",
            "jul": "July",
            "aug": "August",
            "sep": "September",
            "oct": "October",
            "nov": "November",
            "dec": "December",
        }

    def parse(self) -> list[BibEntry]:
        entries: list[BibEntry] = []
        while self.pos < self.size:
            at = self.text.find("@", self.pos)
            if at == -1:
                break
            self.pos = at + 1
            entry_type = self._read_identifier().lower()
            self._skip_ws()
            if self._peek() not in "{(":
                continue
            opener = self._next_char()
            closer = "}" if opener == "{" else ")"

            if entry_type in {"comment", "preamble"}:
                self._consume_block(opener, closer)
                continue
            if entry_type == "string":
                self._parse_string(closer)
                continue

            self._current_entry_type = entry_type
            self._current_entry_key = ""
            self._current_entry_line = self._line_for_pos(at)
            entry = self._parse_entry(entry_type, closer)
            self._current_entry_type = ""
            self._current_entry_key = ""
            if entry is not None:
                entries.append(entry)
        return entries

    def _parse_entry(self, entry_type: str, closer: str) -> BibEntry | None:
        self._skip_ws()
        key = self._read_until_top_level({",", closer}).strip()
        self._current_entry_key = key
        if not key:
            self._consume_until({closer})
            if self._peek() == closer:
                self.pos += 1
            return None
        if self._peek() == closer:
            self.pos += 1
            return BibEntry(entry_type=entry_type, key=key, fields={})
        if self._peek() == ",":
            self.pos += 1

        fields: dict[str, str] = {}
        while self.pos < self.size:
            self._skip_ws_and_commas()
            if self._peek() == closer:
                self.pos += 1
                break
            name = self._read_identifier().lower()
            if not name:
                self._consume_until({",", closer})
                if self._peek() == ",":
                    self.pos += 1
                continue
            self._skip_ws()
            if self._peek() != "=":
                self._consume_until({",", closer})
                if self._peek() == ",":
                    self.pos += 1
                continue
            self.pos += 1
            self._skip_ws()
            fields[name] = self._read_value(closer)
            self._skip_ws()
            if self._peek() == ",":
                self.pos += 1

        return BibEntry(entry_type=entry_type, key=key, fields=fields)

    def _parse_string(self, closer: str) -> None:
        self._skip_ws()
        macro_name = self._read_identifier().lower()
        self._skip_ws()
        if self._peek() == "=":
            self.pos += 1
            self._skip_ws()
            value = self._read_value(closer)
            if macro_name:
                self.macros[macro_name] = value
        self._consume_until({closer})
        if self._peek() == closer:
            self.pos += 1

    def _read_value(self, closer: str) -> str:
        parts: list[str] = [self._read_single_value(closer)]
        self._skip_ws()
        while self._peek() == "#":
            self.pos += 1
            self._skip_ws()
            parts.append(self._read_single_value(closer))
            self._skip_ws()
        return "".join(parts).strip()

    def _read_single_value(self, closer: str) -> str:
        ch = self._peek()
        if ch == "{":
            return self._read_braced()
        if ch == '"':
            return self._read_quoted()
        token = self._read_until_top_level({",", closer, "#"}).strip()
        return self.macros.get(token.lower(), token)

    def _read_braced(self) -> str:
        if self._peek() != "{":
            return ""
        open_pos = self.pos
        self.pos += 1
        depth = 1
        start = self.pos
        reported_nested_field = False
        while self.pos < self.size:
            ch = self.text[self.pos]
            if ch == "\\":
                self.pos += 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    value = self.text[start:self.pos]
                    self.pos += 1
                    return value
            elif (
                ch == ","
                and depth == 1
                and not reported_nested_field
                and _FIELD_SEPARATOR_IN_VALUE.match(self.text[self.pos : self.pos + 80])
            ):
                self._record_issue(
                    line=self._line_for_pos(self.pos),
                    message="Possible missing closing brace before next field.",
                )
                reported_nested_field = True
            self.pos += 1
        self._record_issue(
            line=self._line_for_pos(open_pos),
            message="Unclosed brace in value.",
        )
        return self.text[start:]

    def _read_quoted(self) -> str:
        if self._peek() != '"':
            return ""
        open_pos = self.pos
        self.pos += 1
        out: list[str] = []
        while self.pos < self.size:
            ch = self.text[self.pos]
            if ch == "\\" and self.pos + 1 < self.size:
                out.append(self.text[self.pos : self.pos + 2])
                self.pos += 2
                continue
            if ch == '"':
                self.pos += 1
                break
            out.append(ch)
            self.pos += 1
        else:
            self._record_issue(
                line=self._line_for_pos(open_pos),
                message="Unclosed quoted value.",
            )
        return "".join(out)

    def _consume_block(self, opener: str, closer: str) -> None:
        depth = 1
        while self.pos < self.size and depth > 0:
            ch = self.text[self.pos]
            if ch == "\\":
                self.pos += 2
                continue
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
            self.pos += 1

    def _read_identifier(self) -> str:
        start = self.pos
        while self.pos < self.size:
            ch = self.text[self.pos]
            if ch.isalnum() or ch in "_-:":
                self.pos += 1
                continue
            break
        return self.text[start:self.pos]

    def _read_until_top_level(self, stop_chars: set[str]) -> str:
        start = self.pos
        depth = 0
        while self.pos < self.size:
            ch = self.text[self.pos]
            if ch == "\\":
                self.pos += 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
            elif depth == 0 and ch in stop_chars:
                break
            self.pos += 1
        return self.text[start:self.pos]

    def _consume_until(self, stop_chars: set[str]) -> None:
        while self.pos < self.size and self.text[self.pos] not in stop_chars:
            self.pos += 1

    def _skip_ws(self) -> None:
        while self.pos < self.size:
            ch = self.text[self.pos]
            if ch.isspace():
                self.pos += 1
                continue
            if ch == "%":
                while self.pos < self.size and self.text[self.pos] != "\n":
                    self.pos += 1
                continue
            break

    def _skip_ws_and_commas(self) -> None:
        while self.pos < self.size:
            ch = self.text[self.pos]
            if ch.isspace() or ch == ",":
                self.pos += 1
                continue
            if ch == "%":
                while self.pos < self.size and self.text[self.pos] != "\n":
                    self.pos += 1
                continue
            break

    def _peek(self) -> str:
        if self.pos >= self.size:
            return ""
        return self.text[self.pos]

    def _next_char(self) -> str:
        ch = self._peek()
        if ch:
            self.pos += 1
        return ch

    def _line_for_pos(self, pos: int) -> int:
        return self.text.count("\n", 0, max(0, pos)) + 1

    def _record_issue(self, line: int, message: str) -> None:
        issue = BibParseIssue(
            line=line,
            entry_type=self._current_entry_type or "unknown",
            key=self._current_entry_key,
            message=message,
        )
        if issue not in self.issues:
            self.issues.append(issue)


def parse_bibtex(text: str) -> list[BibEntry]:
    """Parse BibTeX text into a list of entries."""
    return parse_bibtex_with_report(text).entries


def parse_bibtex_with_report(text: str) -> BibParseResult:
    """Parse BibTeX text into a list of entries.

    The parser first attempts a whole-file parse. If that yields fewer entries
    than expected from entry headers, it falls back to chunk parsing per entry
    start so a single malformed entry does not hide later valid entries.
    """
    parser = _BibParser(text)
    parsed = parser.parse()
    issues: list[BibParseIssue] = list(parser.issues)
    headers = _entry_headers(text)
    expected = len(headers)
    if expected == 0 or len(parsed) >= expected:
        return BibParseResult(entries=parsed, issues=_dedupe_issues(issues))

    starts = [header["start"] for header in headers]
    if not starts:
        return BibParseResult(entries=parsed, issues=[])

    recovered: list[BibEntry] = []
    seen: set[tuple[str, str]] = set()
    boundaries = starts + [len(text)]
    for idx, start in enumerate(starts):
        chunk = text[start : boundaries[idx + 1]]
        header = headers[idx]
        chunk_parser = _BibParser(chunk)
        chunk_entries = chunk_parser.parse()
        line_offset = header["line"] - 1
        issues.extend(
            BibParseIssue(
                line=int(issue.line) + line_offset,
                entry_type=issue.entry_type,
                key=issue.key,
                message=issue.message,
            )
            for issue in chunk_parser.issues
        )
        if not chunk_entries:
            issues.append(
                BibParseIssue(
                    line=header["line"],
                    entry_type=header["entry_type"],
                    key=header["key"],
                    message="Malformed entry could not be parsed.",
                )
            )
            continue
        for entry in chunk_entries:
            identity = (entry.entry_type, entry.key)
            if not entry.key or identity in seen:
                continue
            recovered.append(entry)
            seen.add(identity)

    best = recovered if len(recovered) > len(parsed) else parsed
    known = {(entry.entry_type, entry.key) for entry in best}
    reported = {(issue.entry_type, issue.key, issue.line) for issue in issues}
    for header in headers:
        identity = (header["entry_type"], header["key"])
        if identity in known:
            continue
        marker = (header["entry_type"], header["key"], header["line"])
        if marker in reported:
            continue
        issues.append(
            BibParseIssue(
                line=header["line"],
                entry_type=header["entry_type"],
                key=header["key"],
                message="Entry was skipped due to parse errors.",
            )
        )

    return BibParseResult(entries=best, issues=_dedupe_issues(issues))


def _entry_headers(text: str) -> list[dict[str, object]]:
    headers: list[dict[str, object]] = []
    for match in _ENTRY_HEADER.finditer(text):
        entry_type = (match.group("etype") or "").lower()
        if entry_type in {"comment", "string", "preamble"}:
            continue
        key = (match.group("key") or "").strip()
        line = text.count("\n", 0, match.start()) + 1
        headers.append(
            {
                "start": match.start(),
                "line": line,
                "entry_type": entry_type,
                "key": key,
            }
        )
    return headers


def _dedupe_issues(issues: list[BibParseIssue]) -> list[BibParseIssue]:
    deduped: list[BibParseIssue] = []
    seen: set[tuple[int, str, str, str]] = set()
    for issue in issues:
        marker = (issue.line, issue.entry_type, issue.key, issue.message)
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(issue)
    return deduped
