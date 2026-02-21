"""Transform parsed BibTeX entries into publication HTML."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
import re

from .bibtex import BibEntry
from .template import Template

_MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_LATEX_TEXT_MACRO = re.compile(r"\\(?:textit|textbf|emph|texttt|textsc|url)\{([^{}]*)\}")
_LATEX_ACCENT_MACRO = re.compile(
    r"\\[`'\"^~=.]\{?([A-Za-z])\}?|\\(?:u|v|H|c|d|b|k|r|t)\{([A-Za-z])\}|\\[A-Za-z]+\{([A-Za-z])\}"
)
_LATEX_COMMAND = re.compile(r"\\[A-Za-z]+\*?")
_MULTISPACE = re.compile(r"\s+")


def _latex_to_text(value: str) -> str:
    text = value or ""
    text = text.replace(r"\textasteriskcentered", "*")
    text = text.replace(r"\ast", "*")
    text = text.replace(r"\*", "*")
    while True:
        updated = _LATEX_TEXT_MACRO.sub(r"\1", text)
        if updated == text:
            break
        text = updated
    text = _LATEX_ACCENT_MACRO.sub(
        lambda m: m.group(1) or m.group(2) or m.group(3) or "", text
    )
    text = text.replace("\\&", "&")
    text = text.replace("~", " ")
    text = _LATEX_COMMAND.sub("", text)
    text = text.replace("{", "").replace("}", "")
    return _MULTISPACE.sub(" ", text).strip()


def _split_names(raw: str) -> list[str]:
    if not raw:
        return []
    names: list[str] = []
    token: list[str] = []
    depth = 0
    i = 0
    text = raw.strip()
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
            token.append(ch)
            i += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            token.append(ch)
            i += 1
            continue
        if depth == 0 and text[i : i + 5].lower() == " and ":
            names.append("".join(token).strip())
            token = []
            i += 5
            continue
        token.append(ch)
        i += 1
    if token:
        names.append("".join(token).strip())
    return [n for n in names if n]


def _name_parts(name: str) -> tuple[str, str]:
    text = _latex_to_text(name).strip()
    if not text:
        return "", ""
    if "," in text:
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if len(parts) == 1:
            return "", parts[0]
        if len(parts) == 2:
            return parts[1], parts[0]
        # BibTeX form: von Last, Jr, First
        return " ".join(parts[2:]), f"{parts[0]}, {parts[1]}"
    chunks = text.split()
    if len(chunks) == 1:
        return "", chunks[0]
    return " ".join(chunks[:-1]), chunks[-1]


def _format_first_last(first: str, last: str) -> str:
    return " ".join([first, last]).strip()


def _first_initial(first: str) -> str:
    for ch in first:
        if ch.isalpha():
            return f"{ch.upper()}."
    return ""


def _format_last_first(first: str, last: str) -> str:
    initial = _first_initial(first)
    if last and initial:
        return f"{last}, {initial}"
    if last:
        return last
    if initial:
        return initial
    return (last or first).strip()


def _month_number(value: str) -> int:
    if not value:
        return 0
    raw = _latex_to_text(value).lower()
    if raw.isdigit():
        as_int = int(raw)
        if 1 <= as_int <= 12:
            return as_int
    return _MONTHS.get(raw, 0)


def _year_int(value: str) -> int:
    if not value:
        return 0
    text = _latex_to_text(value)
    match = re.search(r"\d{4}", text)
    return int(match.group(0)) if match else 0


def _venue(fields: dict[str, str]) -> str:
    if fields.get("journal"):
        return _latex_to_text(fields["journal"])
    if fields.get("booktitle"):
        return _latex_to_text(fields["booktitle"])
    return ""


def _entry_context(entry: BibEntry, author_name_order: str) -> dict[str, object]:
    fields = entry.fields
    names = _split_names(fields.get("author", "") or fields.get("editor", ""))
    name_parts = [_name_parts(n) for n in names]
    authors_first_last = [_format_first_last(first, last) for first, last in name_parts]
    authors_last_first = [_format_last_first(first, last) for first, last in name_parts]
    title = _latex_to_text(fields.get("title", ""))
    year = _latex_to_text(fields.get("year", ""))
    month = _latex_to_text(fields.get("month", ""))
    url = _latex_to_text(fields.get("url", ""))
    doi = _latex_to_text(fields.get("doi", ""))
    doi_url = f"https://doi.org/{doi}" if doi else ""
    pdf = _latex_to_text(
        fields.get("pdf", "")
        or fields.get("paper_pdf", "")
        or fields.get("pdf_url", "")
        or fields.get("fulltext", "")
    )
    supplementary = _latex_to_text(
        fields.get("supplementary", "")
        or fields.get("supplement", "")
        or fields.get("supplementary_material", "")
    )
    code = _latex_to_text(
        fields.get("code", "")
        or fields.get("code_url", "")
        or fields.get("repository", "")
        or fields.get("repo", "")
    )
    venue = _venue(fields)
    if author_name_order == "last-first":
        authors_selected = authors_last_first
        authors_selected_sep = ", "
    else:
        authors_selected = authors_first_last
        authors_selected_sep = ", "
    authors_display = authors_selected_sep.join(authors_selected)
    return {
        "id": entry.key,
        "type": entry.entry_type,
        "title": title,
        "year": year,
        "month": month,
        "venue": venue,
        "url": url,
        "doi": doi,
        "doi_url": doi_url,
        "pdf": pdf,
        "supplementary": supplementary,
        "code": code,
        "pages": _latex_to_text(fields.get("pages", "")),
        "volume": _latex_to_text(fields.get("volume", "")),
        "number": _latex_to_text(fields.get("number", "")),
        "note": _latex_to_text(fields.get("note", "")),
        # `authors`/`authors_text` follow configured display order to keep
        # older templates compatible with --author-name-order.
        "authors": authors_selected,
        "authors_first_last": authors_first_last,
        "authors_last_first": authors_last_first,
        "authors_text": authors_selected_sep.join(authors_selected),
        "authors_text_first_last": ", ".join(authors_first_last),
        "authors_text_last_first": ", ".join(authors_last_first),
        "authors_display": authors_display,
        "fields": {k: _latex_to_text(v) for k, v in fields.items()},
        "_sort_year": _year_int(fields.get("year", "")),
        "_sort_month": _month_number(fields.get("month", "")),
    }


def render_publications(
    entries: list[BibEntry],
    template_text: str,
    site_title: str = "Publications",
    author_name_order: str = "last-first",
) -> str:
    """Render entries to HTML using a Mustache-style template."""
    if author_name_order not in {"first-last", "last-first"}:
        raise ValueError("author_name_order must be either 'first-last' or 'last-first'.")
    normalized = [_entry_context(e, author_name_order=author_name_order) for e in entries]
    normalized.sort(key=lambda e: (e["_sort_year"], e["_sort_month"]), reverse=True)
    by_year: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in normalized:
        year_label = str(item.get("year") or "Unknown")
        by_year[year_label].append(item)
    year_groups = [
        {"year": year, "entries": grouped}
        for year, grouped in sorted(
            by_year.items(), key=lambda pair: int(pair[0]) if pair[0].isdigit() else -1, reverse=True
        )
    ]
    ctx: dict[str, object] = {
        "site_title": site_title,
        "count": len(normalized),
        "generated_on": date.today().isoformat(),
        "author_name_order": author_name_order,
        "entries": normalized,
        "entries_by_year": year_groups,
    }
    tmpl = Template(template_text)
    return tmpl.render(ctx)
