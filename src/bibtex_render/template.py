"""Small Mustache-like template engine for HTML rendering."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape


class TemplateError(ValueError):
    """Raised when the template is malformed."""


@dataclass(slots=True)
class _TextNode:
    text: str


@dataclass(slots=True)
class _VarNode:
    name: str
    escape_html: bool


@dataclass(slots=True)
class _SectionNode:
    name: str
    children: list[object]
    inverted: bool


class Template:
    """Minimal Mustache-like template.

    Supported tags:
    - {{name}}: escaped variable
    - {{{name}}}: unescaped variable
    - {{#items}}...{{/items}}: section/loop
    - {{^items}}...{{/items}}: inverted section
    """

    def __init__(self, source: str):
        self.source = source
        self.nodes, _ = self._parse(0, None)

    def render(self, context: dict[str, object]) -> str:
        return self._render_nodes(self.nodes, [context])

    def _parse(self, pos: int, expected_end: str | None) -> tuple[list[object], int]:
        nodes: list[object] = []
        src = self.source
        size = len(src)
        while pos < size:
            start = src.find("{{", pos)
            if start == -1:
                nodes.append(_TextNode(src[pos:]))
                pos = size
                break
            if start > pos:
                nodes.append(_TextNode(src[pos:start]))
            if src.startswith("{{{", start):
                end = src.find("}}}", start + 3)
                if end == -1:
                    raise TemplateError("Unclosed triple-brace variable.")
                name = src[start + 3 : end].strip()
                nodes.append(_VarNode(name=name, escape_html=False))
                pos = end + 3
                continue
            end = src.find("}}", start + 2)
            if end == -1:
                raise TemplateError("Unclosed tag.")
            tag = src[start + 2 : end].strip()
            pos = end + 2
            if not tag:
                continue
            marker = tag[0]
            if marker in {"#", "^"}:
                name = tag[1:].strip()
                children, pos = self._parse(pos, name)
                nodes.append(
                    _SectionNode(name=name, children=children, inverted=marker == "^")
                )
                continue
            if marker == "/":
                close_name = tag[1:].strip()
                if expected_end is None:
                    raise TemplateError(f"Unexpected closing tag: {close_name}")
                if close_name != expected_end:
                    raise TemplateError(
                        f"Mismatched closing tag. Expected {expected_end}, got {close_name}."
                    )
                return nodes, pos
            nodes.append(_VarNode(name=tag, escape_html=True))

        if expected_end is not None:
            raise TemplateError(f"Unclosed section: {expected_end}")
        return nodes, pos

    def _render_nodes(self, nodes: list[object], stack: list[object]) -> str:
        parts: list[str] = []
        for node in nodes:
            if isinstance(node, _TextNode):
                parts.append(node.text)
                continue
            if isinstance(node, _VarNode):
                value = self._resolve(node.name, stack)
                if value is None:
                    continue
                text = str(value)
                parts.append(escape(text) if node.escape_html else text)
                continue
            if isinstance(node, _SectionNode):
                value = self._resolve(node.name, stack)
                if node.inverted:
                    if not value:
                        parts.append(self._render_nodes(node.children, stack))
                    continue
                if isinstance(value, list):
                    for item in value:
                        parts.append(self._render_nodes(node.children, [item] + stack))
                    continue
                if isinstance(value, dict):
                    parts.append(self._render_nodes(node.children, [value] + stack))
                    continue
                if value:
                    # For scalar truthy values, render once with existing context.
                    # This matches Mustache behavior and avoids scalar methods
                    # shadowing template keys in parent scopes.
                    parts.append(self._render_nodes(node.children, stack))
        return "".join(parts)

    def _resolve(self, name: str, stack: list[object]) -> object | None:
        if name == ".":
            return stack[0] if stack else None
        for scope in stack:
            found, value = self._lookup(scope, name)
            if found:
                return value
        return None

    @staticmethod
    def _lookup(scope: object, path: str) -> tuple[bool, object | None]:
        parts = path.split(".")
        value = scope
        for part in parts:
            if isinstance(value, dict):
                if part not in value:
                    return False, None
                value = value[part]
                continue
            if hasattr(value, part):
                value = getattr(value, part)
                continue
            return False, None
        return True, value
