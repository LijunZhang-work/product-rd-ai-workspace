"""Verify the expanded workspace without requiring Git or running product tools."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import zipfile

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = '总览与规则/工作区文件清单.json'
REPORT = '总览与规则/核验结果.json'


def sha256_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def is_payload(rel):
    if rel in {MANIFEST, REPORT}:
        return False
    parts = Path(rel).parts
    if any(p in {'.git', '__pycache__', '.venv', 'node_modules'} for p in parts):
        return False
    return not (parts[0] == '交付包' and rel.endswith('.zip'))


def local_links(path):
    fence = None
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        opening = re.match(r'^\s*(`{3,}|~{3,})', line)
        if opening:
            marker = opening.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        for match in re.finditer(r'!?\[[^\]\n]*\]\(([^\n)]*)\)', line):
            target = match.group(1).strip('<>')
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            yield number, target, unquote(parts.path)


def verify(root):
    root = Path(root).resolve()
    data = json.loads((root / MANIFEST).read_text(encoding='utf-8'))
    records = data['files']
    errors = []
    if len({r['path'] for r in records}) != len(records):
        errors.append('Duplicate manifest path')
    expected = {r['path'] for r in records}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and is_payload(p.relative_to(root).as_posix())}
    for rel in sorted(actual - expected):
        errors.append('File not inventoried: ' + rel)
    archives = 0
    for r in records:
        p = (root / r['path']).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            errors.append('Missing or out-of-root file: ' + r['path'])
            continue
        if p.stat().st_size != r['size_bytes'] or sha256_file(p) != r['sha256']:
            errors.append('Content mismatch: ' + r['path'])
        if p.suffix in {'.zip', '.whl'}:
            archives += 1
            try:
                with zipfile.ZipFile(p) as z:
                    bad = z.testzip()
                    if bad:
                        errors.append('ZIP CRC mismatch: ' + r['path'])
            except (OSError, zipfile.BadZipFile) as e:
                errors.append('Archive error: ' + r['path'] + ': ' + str(e))
    links = 0
    for rel in sorted(actual):
        if not rel.endswith('.md'):
            continue
        p = root / rel
        for number, target, decoded in local_links(p):
            links += 1
            dest = (p.parent / decoded).resolve()
            if not dest.is_relative_to(root) or not dest.exists():
                errors.append(f'Broken local link: {rel}:{number}: {target}')
    return dict(ok=not errors, files_checked=len(records), archives_checked=archives,
                local_file_links_checked=links, git_required=False,
                product_tests_executed=False, external_urls_checked=False,
                delivery_zip_files_excluded=True, errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.root)
        text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.out:
            with args.out.open('x', encoding='utf-8') as f:
                f.write(text)
        print(text, end='')
        return 0 if result['ok'] else 1
    except (OSError, ValueError, KeyError, TypeError) as e:
        print('Verification error: ' + str(e), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
