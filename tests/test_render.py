import unittest

from bibtex_render.bibtex import parse_bibtex, parse_bibtex_with_report
from bibtex_render.cli import main
from bibtex_render.render import render_publications
from io import StringIO
from pathlib import Path
import tempfile
from contextlib import redirect_stderr


class RenderTest(unittest.TestCase):
    def test_render_publications_groups_by_year(self) -> None:
        text = """
@inproceedings{a2024,
  author = {Doe, Jane and Smith, Alex},
  title = {Paper A},
  booktitle = {Conf A},
  year = {2024},
  supplementary = {https://example.org/supp-a},
  code = {https://github.com/example/paper-a}
}

@article{b2023,
  author = {Roe, Riley},
  title = {Paper B},
  journal = {Journal B},
  year = {2023}
}
"""
        entries = parse_bibtex(text)
        template = """
<h1>{{site_title}}</h1>
{{#entries_by_year}}<h2>{{year}}</h2>{{#entries}}<p>{{id}}|{{authors_text}}|{{title}}</p>{{/entries}}{{/entries_by_year}}
"""
        html = render_publications(entries, template, site_title="Publications")
        self.assertIn("<h2>2024</h2>", html)
        self.assertIn("a2024|Doe, J., Smith, A.|Paper A", html)
        self.assertIn("<h2>2023</h2>", html)

    def test_render_supports_supplementary_and_code_fields(self) -> None:
        text = """
@article{a2024,
  author = {Doe, Jane},
  title = {Paper A},
  year = {2024},
  pdf = {https://example.org/paper.pdf},
  supplementary = {https://example.org/supp},
  code = {https://github.com/example/paper}
}
"""
        entries = parse_bibtex(text)
        template = "{{#entries}}<p>{{pdf}}|{{supplementary}}|{{code}}</p>{{/entries}}"
        html = render_publications(entries, template)
        self.assertIn(
            "https://example.org/paper.pdf|https://example.org/supp|https://github.com/example/paper",
            html,
        )

    def test_render_supports_last_first_author_order(self) -> None:
        text = """
@inproceedings{a2024,
  author = {Doe, Jane and Smith, Alex},
  title = {Paper A},
  booktitle = {Conf A},
  year = {2024}
}
"""
        entries = parse_bibtex(text)
        template = "{{#entries}}<p>{{authors_display}}|{{authors_text}}|{{authors_text_last_first}}</p>{{/entries}}"
        html = render_publications(entries, template, author_name_order="last-first")
        self.assertIn(
            "Doe, J., Smith, A.|Doe, J., Smith, A.|Doe, J., Smith, A.",
            html,
        )

    def test_default_template_links_title_to_pdf_when_present(self) -> None:
        text = """
@article{a2024,
  author = {Doe, Jane},
  title = {Paper With PDF},
  year = {2024},
  pdf = {https://example.org/paper.pdf}
}

@article{b2023,
  author = {Roe, Riley},
  title = {Paper Without PDF},
  year = {2023}
}
"""
        entries = parse_bibtex(text)
        template_path = Path("/Users/maxs/bibtex-render/src/bibtex_render/default_template.mustache")
        template = template_path.read_text(encoding="utf-8")
        html = render_publications(entries, template)
        self.assertIn(
            '<a class="publication-title publication-title-link" href="https://example.org/paper.pdf">"Paper With PDF"</a>.',
            html,
        )
        self.assertIn('<span class="publication-title">"Paper Without PDF"</span>.', html)

    def test_venue_prefers_journal_then_booktitle(self) -> None:
        text = """
@article{j2024,
  author = {Doe, Jane},
  title = {Journal First},
  journal = {Journal X},
  booktitle = {Booktitle Should Not Win},
  year = {2024}
}

@inproceedings{b2023,
  author = {Roe, Riley},
  title = {Booktitle Used},
  booktitle = {Conference Y},
  publisher = {Publisher Should Not Be Used},
  year = {2023}
}
"""
        entries = parse_bibtex(text)
        template = "{{#entries}}<p>{{id}}|{{venue}}</p>{{/entries}}"
        html = render_publications(entries, template)
        self.assertIn("j2024|Journal X", html)
        self.assertIn("b2023|Conference Y", html)
        self.assertNotIn("Publisher Should Not Be Used", html)

    def test_parser_recovers_entries_after_malformed_block(self) -> None:
        text = """
@article{ok1,
  author = {Doe, Jane},
  title = {Valid One},
  year = {2022}
}

@article{broken,
  author = {Bad, Entry},
  title = {This title has an unclosed brace {oops},
  year = {2021}
}

@inproceedings{ok2,
  author = {Smith, Alex},
  title = {Valid Two},
  booktitle = {Conf},
  year = {2020}
}
"""
        entries = parse_bibtex(text)
        ids = {entry.key for entry in entries}
        self.assertIn("ok1", ids)
        self.assertIn("ok2", ids)

    def test_parser_reports_malformed_entries(self) -> None:
        text = """
@article{ok1,
  author = {Doe, Jane},
  title = {Valid One},
  year = {2022}
}

@article{broken,
  author = {Bad, Entry},
  title = {This title has an unclosed brace {oops},
  year = {2021}
}

@inproceedings{ok2,
  author = {Smith, Alex},
  title = {Valid Two},
  booktitle = {Conf},
  year = {2020}
}
"""
        result = parse_bibtex_with_report(text)
        ids = {entry.key for entry in result.entries}
        self.assertIn("ok1", ids)
        self.assertIn("ok2", ids)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].key, "broken")
        self.assertEqual(result.issues[0].entry_type, "article")

    def test_cli_prints_warning_and_strict_fails(self) -> None:
        bib = """
@article{ok1,
  author = {Doe, Jane},
  title = {Valid One},
  year = {2022}
}

@article{broken,
  author = {Bad, Entry},
  title = {This title has an unclosed brace {oops},
  year = {2021}
}

@inproceedings{ok2,
  author = {Smith, Alex},
  title = {Valid Two},
  booktitle = {Conf},
  year = {2020}
}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bib_path = Path(tmpdir) / "input.bib"
            out_path = Path(tmpdir) / "out.html"
            bib_path.write_text(bib, encoding="utf-8")
            err = StringIO()
            with redirect_stderr(err):
                code = main([str(bib_path), "-o", str(out_path)])
            self.assertEqual(code, 0)
            self.assertIn("warning: malformed BibTeX entry", err.getvalue())

            err = StringIO()
            with redirect_stderr(err):
                strict_code = main([str(bib_path), "-o", str(out_path), "--strict"])
            self.assertEqual(strict_code, 2)


if __name__ == "__main__":
    unittest.main()
