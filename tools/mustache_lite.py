#!/usr/bin/env python3
"""Mustache-Teilmenge für die Partials der Bewerbungsmappe (nur Python-Standardbibliothek).

Unterstützt:
  {{name}}            Wert, HTML-escaped        {{{name}}}        Wert roh (nur für CSS, Schrift, Symbole)
  {{#name}}…{{/name}} Abschnitt                 {{^name}}…{{/name}} Abschnitt, wenn der Wert leer ist
  {{> partial}}       anderes Partial            {{! Text }}       Kommentar, erscheint nicht in der Ausgabe
  {{.}}               aktuelles Element          a.b               Punktpfad

Mit Absicht anders als Mustache:
- Strenge Schlüssel: Ein Name wird nur im aktuellen Kontext gesucht, nie in äußeren Ebenen. Fehlt er, bricht
  das Rendern mit RenderError ab (Partial, Zeile, Schlüssel). Das View-Model setzt deshalb jeden Schlüssel,
  den ein Partial nennt, notfalls mit None. So kann kein Wert unbemerkt aus einer äußeren Ebene einsickern.
- Abschnitt über einem dict: der Inhalt sieht nur dieses dict. Über einer Liste: einmal je Element. Über einem
  anderen wahren Wert (True, Text, Zahl): einmal, im selben Kontext.
- Steht ein Abschnitts-, Kommentar- oder Partial-Tag allein in seiner Zeile, entfällt die Zeile. Ein Partial
  bringt seine Einrückung selbst mit. Wird es mitten in einer Zeile eingesetzt, entfällt sein letzter
  Zeilenumbruch.
"""
from __future__ import annotations

import html
import re

TAG = re.compile(r'\{\{\{\s*([\w.\-]+)\s*\}\}\}|\{\{\s*([#^/>!]?)\s*(.*?)\s*\}\}', re.S)
NAME = re.compile(r'\.|[\w\-]+(\.[\w\-]+)*')


class RenderError(Exception):
    pass


def parse(source: str, name: str = '?') -> list:
    """Quelltext -> Knotenliste: ('text', s) · ('var', pfad, roh, zeile) · ('section', pfad, umgekehrt, kinder, zeile)
    · ('partial', name, allein_in_zeile, zeile)."""
    root: list = []
    stack: list[tuple[list, str, int]] = []  # (Knotenliste der Elternebene, offener Abschnitt, Zeile)
    nodes, pos = root, 0
    for m in TAG.finditer(source):
        raw, kind, body = m.group(1), m.group(2) or '', m.group(3) or ''
        line = source.count('\n', 0, m.start()) + 1
        start, end = m.start(), m.end()
        if not raw and kind:  # Tag allein in der Zeile: Einrückung davor und Zeilenende danach entfallen
            line_start = source.rfind('\n', 0, start) + 1
            line_end = source.find('\n', end)
            line_end = len(source) if line_end == -1 else line_end
            alone = not source[line_start:start].strip() and not source[end:line_end].strip() and line_start >= pos
            if alone:
                start, end = line_start, min(line_end + 1, len(source))
        else:
            alone = False
        if source[pos:start]:
            nodes.append(('text', source[pos:start]))
        pos = end
        if raw:
            nodes.append(('var', raw, True, line))
        elif kind == '!':
            continue
        elif not NAME.fullmatch(body):
            raise RenderError(f'{name}:{line}: ungültiges Tag „{m.group(0)}“')
        elif kind == '>':
            nodes.append(('partial', body, alone, line))
        elif kind in ('#', '^'):
            children: list = []
            nodes.append(('section', body, kind == '^', children, line))
            stack.append((nodes, body, line))
            nodes = children
        elif kind == '/':
            if not stack or stack[-1][1] != body:
                raise RenderError(f'{name}:{line}: {{{{/{body}}}}} schließt keinen offenen Abschnitt')
            nodes = stack.pop()[0]
        else:
            nodes.append(('var', body, False, line))
    if stack:
        raise RenderError(f'{name}:{stack[-1][2]}: Abschnitt „{stack[-1][1]}“ ist nicht geschlossen')
    if source[pos:]:
        nodes.append(('text', source[pos:]))
    return root


class Renderer:
    """Hält die Partials (Name -> Quelltext) und rendert eines davon mit einem Kontext."""

    def __init__(self, partials: dict[str, str]):
        self.sources = partials
        self.parsed = {name: parse(text, name) for name, text in partials.items()}

    def lookup(self, context, path: str, where: str):
        if path == '.':
            return context
        value = context
        for key in path.split('.'):
            if not isinstance(value, dict) or key not in value:
                have = ', '.join(sorted(value)) if isinstance(value, dict) else type(value).__name__
                raise RenderError(f'{where}: Schlüssel „{path}“ fehlt im Kontext (vorhanden: {have}). '
                                  'Das View-Model muss jeden Schlüssel setzen, notfalls mit None.')
            value = value[key]
        return value

    def render(self, name: str, context) -> str:
        if name not in self.parsed:
            raise RenderError(f'Partial „{name}“ fehlt')
        out: list[str] = []
        self._run(self.parsed[name], context, name, out)
        return ''.join(out)

    def _run(self, nodes: list, context, name: str, out: list[str]) -> None:
        for node in nodes:
            kind = node[0]
            if kind == 'text':
                out.append(node[1])
            elif kind == 'var':
                value = self.lookup(context, node[1], f'{name}:{node[3]}')
                if value is not None:
                    out.append(str(value) if node[2] else html.escape(str(value), quote=True))
            elif kind == 'partial':
                text = self.render(node[1], context)
                out.append(text if node[2] or not text.endswith('\n') else text[:-1])
            else:
                _, path, inverted, children, line = node
                value = self.lookup(context, path, f'{name}:{line}')
                if inverted:
                    if not value:
                        self._run(children, context, name, out)
                elif isinstance(value, list):
                    for item in value:
                        self._run(children, item, name, out)
                elif isinstance(value, dict):
                    if value:
                        self._run(children, value, name, out)
                elif value:
                    self._run(children, context, name, out)

    def outline(self, name: str) -> list[str]:
        """Alle Schlüssel, die ein Partial nennt, mit Ebene: „a“, „a[].b“ (Abschnitt), „> partial“."""
        found: list[str] = []

        def walk(nodes: list, prefix: str) -> None:
            for node in nodes:
                if node[0] == 'var':
                    found.append(prefix + node[1])
                elif node[0] == 'partial':
                    found.append(f'{prefix}> {node[1]}')
                elif node[0] == 'section':
                    found.append(prefix + node[1])
                    walk(node[3], f'{prefix}{node[1]}[].')
        walk(self.parsed[name], '')
        return list(dict.fromkeys(found))
