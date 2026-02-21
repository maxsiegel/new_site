# bibtex-render

Render a BibTeX file into publication HTML using a customizable template.

## What it does

- Parses a `.bib` file with your citations.
- Normalizes common fields (`author`, `title`, `year`, `journal`/`booktitle`, `url`, `doi`).
- Supports extra link fields for `pdf`, `supplementary` material, and `code`.
- Supports author display order via `--author-name-order` (default: `last-first`).
  - `last-first` renders as `Last, F.` (e.g., `Doe, J., Smith, A.`).
- Renders HTML with a Mustache-style template so you can control layout and CSS classes.

## Install

```bash
pip install -e .
```

## Usage

```bash
bibtex-render examples/sample.bib -o publications.html
```

Use a custom template:

```bash
bibtex-render my-papers.bib --template my-template.mustache --title "Selected Publications" -o site/publications.html
```

Use first-name-first author display:

```bash
bibtex-render my-papers.bib --author-name-order first-last -o publications.html
```

Malformed entry reporting:

```bash
bibtex-render my-papers.bib -o publications.html
# warnings are printed to stderr with line/type/key details
```

Fail fast on malformed entries:

```bash
bibtex-render my-papers.bib -o publications.html --strict
```

Render to stdout:

```bash
bibtex-render my-papers.bib --template my-template.mustache
```

## Template language

The renderer uses a small Mustache-like syntax:

- `{{field}}` escaped variable
- `{{{field}}}` unescaped variable
- `{{#section}}...{{/section}}` section / loop
- `{{^section}}...{{/section}}` inverted section

Top-level fields available:

- `site_title`
- `count`
- `generated_on`
- `entries` (flat list)
- `entries_by_year` (grouped list)

Per-entry fields:

- `id`, `type`, `title`, `year`, `month`, `venue`
- `authors`, `authors_text` (both follow selected `--author-name-order`)
- `authors_first_last`, `authors_last_first`
- `authors_text_first_last`, `authors_text_last_first`, `authors_display`
- `url`, `doi`, `doi_url`, `pdf`, `supplementary`, `code`
- `pages`, `volume`, `number`, `note`
- `fields` (all parsed fields as a map)

## Default template

The built-in template lives at:

- `src/bibtex_render/default_template.mustache`

Copy it and modify the markup/classes to fit your academic website style.

## Quick test

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"
```
