# CV (moderncv)

Starter CV built with the `moderncv` LaTeX template.

## Files

- `cv.tex`: main CV source

## Build

```bash
cd /Users/maxs/personal/cv
latexmk -pdf cv.tex
```

With `latexmkrc`, build artifacts go to `build/` and `cv.pdf` is written to
`/Users/maxs/personal/cv`.

If `latexmk` is not installed, use a manual fallback:

```bash
cd /Users/maxs/personal/cv
pdflatex cv.tex
pdflatex cv.tex
```

Output file: `cv.pdf`
