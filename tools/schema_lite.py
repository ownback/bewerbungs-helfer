#!/usr/bin/env python3
"""JSON-Schema-Prüfung für die Schemas des Bewerbungshelfers (nur Python-Standardbibliothek).

Unterstützt genau die Schlüsselwörter, die die Schemas unter assets/schemas/ verwenden (Draft 2020-12):
  type, enum, const, required, properties, additionalProperties, items, prefixItems, minItems, maxItems,
  minLength, maxLength, pattern, format (date, date-time, email, uri), minimum, maximum, $ref (nur innerhalb
  der Datei, „#/…“), allOf, oneOf, if/then/else.
Reine Beschreibungen ($schema, $id, $defs, title, description, default, examples, $comment) werden übergangen.
Jedes andere Schlüsselwort bricht mit SchemaError ab: Ein Schema darf nichts verlangen, was hier still
ungeprüft bliebe. Dann das Schlüsselwort hier ergänzen oder das Schema anders ausdrücken.

  errors(instance, schema) -> Liste aus (Pfad, Meldung), leer = gültig

Aufruf zum Ausprobieren: python3 tools/schema_lite.py <schema.json> <daten.json>
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from urllib.parse import urlsplit

CHECKED = {'type', 'enum', 'const', 'required', 'properties', 'additionalProperties', 'items', 'prefixItems',
           'minItems', 'maxItems', 'minLength', 'maxLength', 'pattern', 'format', 'minimum', 'maximum', '$ref',
           'allOf', 'oneOf', 'if', 'then', 'else'}
ANNOTATIONS = {'$schema', '$id', '$defs', 'title', 'description', 'default', 'examples', '$comment'}
TYPES = {'string': str, 'object': dict, 'array': list, 'boolean': bool, 'null': type(None)}


class SchemaError(Exception):
    """Das Schema selbst ist fehlerhaft oder nutzt etwas, das diese Prüfung nicht kennt."""


def type_ok(value, name: str) -> bool:
    if name == 'integer':
        return (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and value.is_integer())
    if name == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name not in TYPES:
        raise SchemaError(f'unbekannter type „{name}“')
    return isinstance(value, TYPES[name])


def same(a, b) -> bool:
    """Gleichheit nach JSON: true ist nicht 1, 1 ist 1.0, Listen und Objekte elementweise."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(v, b[k]) for k, v in a.items())
    return a == b


def format_ok(value: str, name: str) -> bool:
    try:
        if name == 'date':
            return bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)) and bool(dt.date.fromisoformat(value))
        if name == 'date-time':
            return bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})', value)) \
                and bool(dt.datetime.fromisoformat(value.replace('Z', '+00:00').replace('z', '+00:00')))
        if name == 'email':
            return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', value))
        if name == 'uri':
            parts = urlsplit(value)
            return bool(parts.scheme) and bool(parts.netloc or parts.path) and not re.search(r'\s', value)
    except ValueError:
        return False
    raise SchemaError(f'unbekanntes format „{name}“')


def resolve(ref: str, root: dict):
    if not ref.startswith('#/'):
        raise SchemaError(f'$ref „{ref}“: nur Verweise innerhalb der Datei (#/…) werden unterstützt')
    node = root
    for key in ref[2:].split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        if not isinstance(node, dict) or key not in node:
            raise SchemaError(f'$ref „{ref}“ zeigt ins Leere')
        node = node[key]
    return node


def show(value) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 60 else text[:57] + '…'


def errors(instance, schema, root=None, path: str = '') -> list[tuple[str, str]]:
    """Alle Verstöße von instance gegen schema als (Pfad, Meldung); Pfad wie „person/address/street“."""
    root = schema if root is None else root
    out: list[tuple[str, str]] = []
    where = path or '(root)'
    if schema is True:
        return out
    if schema is False:
        return [(where, 'ist hier nicht erlaubt')]
    if not isinstance(schema, dict):
        raise SchemaError(f'Schema bei {where} ist kein Objekt')
    unknown = set(schema) - CHECKED - ANNOTATIONS
    if unknown:
        raise SchemaError(f'Schlüsselwort {", ".join(sorted(unknown))} bei {where} kennt tools/schema_lite.py nicht')

    def child(key) -> str:
        return f'{path}/{key}' if path else str(key)

    if '$ref' in schema:
        out += errors(instance, resolve(schema['$ref'], root), root, path)
    if 'type' in schema:
        names = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(type_ok(instance, n) for n in names):
            out.append((where, f'{show(instance)} hat nicht den Typ {" oder ".join(names)}'))
    if 'enum' in schema and not any(same(instance, x) for x in schema['enum']):
        out.append((where, f'{show(instance)} ist keiner der erlaubten Werte {show(schema["enum"])}'))
    if 'const' in schema and not same(instance, schema['const']):
        out.append((where, f'{show(instance)} muss {show(schema["const"])} sein'))
    if isinstance(instance, str):
        if len(instance) < schema.get('minLength', 0):
            out.append((where, f'{show(instance)} ist kürzer als {schema["minLength"]} Zeichen'))
        if 'maxLength' in schema and len(instance) > schema['maxLength']:
            out.append((where, f'ist länger als {schema["maxLength"]} Zeichen'))
        if 'pattern' in schema and not re.search(schema['pattern'], instance):
            out.append((where, f'{show(instance)} passt nicht zum Muster {schema["pattern"]}'))
        if 'format' in schema and not format_ok(instance, schema['format']):
            out.append((where, f'{show(instance)} ist kein gültiges {schema["format"]}'))
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if 'minimum' in schema and instance < schema['minimum']:
            out.append((where, f'{instance} ist kleiner als {schema["minimum"]}'))
        if 'maximum' in schema and instance > schema['maximum']:
            out.append((where, f'{instance} ist größer als {schema["maximum"]}'))
    if isinstance(instance, list):
        if len(instance) < schema.get('minItems', 0):
            out.append((where, f'hat {len(instance)} Einträge, mindestens {schema["minItems"]} nötig'))
        if 'maxItems' in schema and len(instance) > schema['maxItems']:
            out.append((where, f'hat {len(instance)} Einträge, höchstens {schema["maxItems"]} erlaubt'))
        prefix = schema.get('prefixItems', [])
        for i, item in enumerate(instance):
            if i < len(prefix):
                out += errors(item, prefix[i], root, child(i))
            elif 'items' in schema:
                out += errors(item, schema['items'], root, child(i))
    if isinstance(instance, dict):
        props = schema.get('properties', {})
        out += [(where, f'Pflichtfeld „{key}“ fehlt') for key in schema.get('required', []) if key not in instance]
        for key, value in instance.items():
            if key in props:
                out += errors(value, props[key], root, child(key))
            elif 'additionalProperties' in schema:
                extra = schema['additionalProperties']
                if extra is False:
                    out.append((where, f'Feld „{key}“ kennt das Schema nicht'))
                else:
                    out += errors(value, extra, root, child(key))
    for sub in schema.get('allOf', []):
        out += errors(instance, sub, root, path)
    if 'oneOf' in schema:
        results = [errors(instance, sub, root, path) for sub in schema['oneOf']]
        valid = sum(1 for r in results if not r)
        if valid != 1:
            detail = '; '.join(msg for r in results for _, msg in r[:1])
            out.append((where, f'passt zu {valid} statt genau einer der {len(results)} Varianten'
                               + (f' ({detail})' if detail and not valid else '')))
    if 'if' in schema:
        branch = 'then' if not errors(instance, schema['if'], root, path) else 'else'
        if branch in schema:
            out += errors(instance, schema[branch], root, path)
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(__doc__)
        return 1
    with open(args[0], encoding='utf-8') as fh:
        schema = json.load(fh)
    with open(args[1], encoding='utf-8') as fh:
        data = json.load(fh)
    found = errors(data, schema)
    for where, message in found:
        print(f'{where}: {message}')
    print(f'{args[1]}: {"gültig" if not found else f"{len(found)} Verstöße"}')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
