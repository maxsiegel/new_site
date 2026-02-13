"""CLI for rendering BibTeX files into HTML."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .bibtex import parse_bibtex_with_report
from .render import render_publications


def _default_template_path() -> Path:
    return Path(__file__).with_name("default_template.mustache")


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bibtex-render",
        description="Render a BibTeX file into HTML for publication pages.",
    )
    parser.add_argument("bibtex_file", help="Path to input .bib file")
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to output HTML file. Use '-' for stdout (default).",
    )
    parser.add_argument(
        "-t",
        "--template",
        help="Path to Mustache template file. Defaults to built-in template.",
    )
    parser.add_argument(
        "--title",
        default="Publications",
        help="Page/section title available to template as {{site_title}}.",
    )
    parser.add_argument(
        "--author-name-order",
        choices=["first-last", "last-first"],
        default="last-first",
        help="Display author names in first-last or last-first order.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with an error if any malformed entries are detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    bib_path = Path(args.bibtex_file)
    if not bib_path.exists():
        parser.error(f"BibTeX file does not exist: {bib_path}")

    template_path = Path(args.template) if args.template else _default_template_path()
    if not template_path.exists():
        parser.error(f"Template file does not exist: {template_path}")

    bib_text = _read_file(bib_path)
    template_text = _read_file(template_path)
    parse_result = parse_bibtex_with_report(bib_text)
    entries = parse_result.entries
    if parse_result.issues:
        for issue in parse_result.issues:
            key_part = f", key={issue.key}" if issue.key else ""
            sys.stderr.write(
                f"warning: malformed BibTeX entry at line {issue.line} "
                f"(type={issue.entry_type}{key_part}): {issue.message}\n"
            )
        if args.strict:
            return 2

    html = render_publications(
        entries,
        template_text,
        site_title=args.title,
        author_name_order=args.author_name_order,
    )

    if args.output == "-":
        sys.stdout.write(html)
        if not html.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    out_path = Path(args.output)
    out_path.write_text(html, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
