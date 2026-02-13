Edit sources in `src/` and served assets in `public/`.

Update publications HTML from BibTeX:
`bibtex-render -t ~/bibtex-render/templates/personal.mustache src/pubs.bib -o src/pubs.html`

Build assembled page:
`./scripts/build-index.sh`

Deploy to MIT:
`./scripts/deploy.sh <kerberos>`
