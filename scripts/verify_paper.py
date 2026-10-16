"""Verify review artifacts and exact examples, not empirical literature claims.

Adapted from AnimaFoundry's Internet of Intelligence review verifier (MIT).
The release manifest excludes itself and contains only the explicit allowlist.
"""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import combinations
import json
from pathlib import Path, PurePosixPath
import re
import sys

from pypdf import PdfReader
from identifiability_example import calculate

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FILES = {
    '.github/workflows/validate.yml', '.gitignore', 'CITATION.cff', 'LICENSE',
    'LICENSE-CODE', 'LICENSE-TEXT', 'METHODS.md', 'README.md', 'RELEASE_NOTES.md',
    'SOURCE_AND_RIGHTS.md', 'figures/crossmodal_loop.svg',
    'identifiability_example.json', 'manuscript.md', 'paper.md', 'paper.pdf',
    'references.json', 'requirements.txt', 'scripts/build_paper.py',
    'scripts/identifiability_example.py', 'scripts/verify_paper.py',
}
EXPECTED_CASES = {
    'silent_channel': (4, 1, ((4, 0), (0, 0)), F(0)),
    'collinear_channels': (4, 1, ((4, 4), (4, 4)), F(0)),
    'crossed_variation': (4, 2, ((4, 0), (0, 4)), F(16)),
    'sparse_but_spanning': (4, 2, ((2, 0), (0, 2)), F(4)),
    'nearly_collinear': (
        4, 2, ((4, F(201, 50)), (F(201, 50), F(20201, 5000))), F(1, 2500)),
    'collinear_repeated_100_times': (400, 1, ((400, 400), (400, 400)), F(0)),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def normalized(text):
    return re.sub(r'\s+', '', text)


def pdf_text(path):
    reader = PdfReader(path)
    require(not reader.is_encrypted, 'PDF must be readable')
    texts = [page.extract_text() or '' for page in reader.pages]
    require(texts and all(len(t) > 100 for t in texts), 'Blank or incomplete page')
    require(all('Not peer reviewed' in t for t in texts), 'Missing status footer')
    require(all('\u25a0' not in t and '\ufffd' not in t for t in texts), 'Missing-glyph marker')
    return texts


def verify_examples(source):
    saved = json.loads((ROOT / 'identifiability_example.json').read_text(encoding='utf-8'))
    require(saved == calculate(), 'Saved calculation differs from implementation')
    cases = {case['name']: case for case in saved['cases']}
    require(len(saved['cases']) == len(cases) == 6, 'Expected six distinct exact examples')
    require(set(cases) == set(EXPECTED_CASES), 'Unexpected example names')
    alternatives = {
        'silent_channel': (F(2), F(99)),
        'collinear_channels': (F(5), F(0)),
        'collinear_repeated_100_times': (F(5), F(0)),
    }
    for name, (rows, expected_rank, expected_gram, expected_det) in EXPECTED_CASES.items():
        case = cases[name]
        if name == 'collinear_repeated_100_times':
            require(case['construction'] == 'collinear_channels design repeated 100 times',
                    'Unexpected repeated-design construction')
            raw = cases['collinear_channels']['design'] * 100
        else:
            raw = case['design']
        x = [[F(value) for value in row] for row in raw]
        require(len(x) == case['rows'] == rows and case['columns'] == 2,
                'Design size mismatch: ' + name)
        require(all(len(row) == 2 for row in x), 'Expected two-column design: ' + name)
        # A separate method from the example's Gaussian elimination: minors
        # determine rank, and Cauchy-Binet determines the Gram determinant.
        minors = [a[0] * b[1] - a[1] * b[0] for a, b in combinations(x, 2)]
        independent_rank = 2 if any(minors) else int(any(v for row in x for v in row))
        require(independent_rank == case['rank'] == expected_rank, 'Rank mismatch: ' + name)
        determinant = sum(value * value for value in minors)
        require(determinant == F(case['gram_determinant']) == expected_det,
                'Determinant mismatch: ' + name)
        gram = [[sum(row[i] * row[j] for row in x) for j in range(2)] for i in range(2)]
        require(gram == [[F(v) for v in row] for row in case['gram']]
                == [list(row) for row in expected_gram], 'Gram mismatch: ' + name)
        targets = [2 * row[0] + 3 * row[1] for row in x]
        if 'target' in case:
            require(targets == [F(v) for v in case['target']], 'Target mismatch: ' + name)
        if name in alternatives:
            alternative = tuple(F(v) for v in case['alternative_theta'])
            require(alternative == alternatives[name], 'Alternative coefficient mismatch: ' + name)
            delta = (alternative[0] - 2, alternative[1] - 3)
            require(any(delta), 'Alternative must differ from generating coefficients')
            require(all(row[0] * delta[0] + row[1] * delta[1] == 0 for row in x),
                    'Claimed null direction changes predictions: ' + name)
            require(case['indistinguishable_from_theta_2_3'] is True,
                    'Missing ambiguity acknowledgement: ' + name)

    crossed = [[F(v) for v in row] for row in cases['crossed_variation']['design']]
    targets = [F(v) for v in cases['crossed_variation']['target']]
    residual = [row[0] * 2 + row[1] * 3 - target for row, target in zip(crossed, targets)]
    gradient = [sum(row[j] * value for row, value in zip(crossed, residual)) for j in range(2)]
    require(gradient == [F(0), F(0)], 'Exact-fit gradient is not zero')
    require(gradient == [F(v) for v in saved['full_rank_exact_fit_gradient']],
            'Reported gradient differs from independently calculated residual gradient')
    require(saved['label_noise_changes_design_rank'] is False, 'Fixed-design noise statement changed')
    require(saved['design_energy_matched'] is False, 'Examples are not energy matched')

    # Lock the displayed conventions; these are checks of this illustration,
    # not a symbolic proof system or empirical population-model validation.
    equations = [
        'L(theta) = (1/2) ||X theta - y||^2',
        'gradient L = X^T (X theta - y)', 'Hessian L = X^T X',
        'dN/dt = a N - b N P', 'dP/dt = c N P - d P',
        'N* = d/c,  P* = a/b', 'N*/P* = (b d)/(a c)',
    ]
    for equation in equations:
        require(equation in source, 'Displayed mathematical convention changed: ' + equation)
    for a, b, c, d, expected_ratio in [(F(1), F(1), F(1), F(2), F(2)),
                                      (F(1), F(1), F(1), F(1), F(1))]:
        n_star, p_star = d / c, a / b
        require(a * n_star - b * n_star * p_star == 0, 'Prey equilibrium residual')
        require(c * n_star * p_star - d * p_star == 0, 'Predator equilibrium residual')
        require(n_star / p_star == b * d / (a * c) == expected_ratio,
                'Illustrative equilibrium ratio mismatch')
    return len(cases)


def verify_pdf_coverage(source, refs, unique, texts):
    body_pages = [re.sub(
        r'AnimaFoundry \| Review preprint v1\.0\.0 \| Not peer reviewed\s*\d+\s*',
        '', text) for text in texts]
    whole = normalized('\n'.join(body_pages))

    def cleaned(text):
        text = re.sub(r'\[@([A-Z0-9]+)\]',
                      lambda match: f'[{unique.index(match.group(1)) + 1}]', text)
        return text.replace('**', '')

    counts = {'headings': 0, 'paragraphs': 0, 'table_cells': 0, 'equation_lines': 0}

    def covered(value, kind):
        require(normalized(cleaned(value)) in whole, 'Missing rendered ' + kind + ': ' + value[:90])
        counts[kind] += 1

    lines, i = source.splitlines(), 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('!['):
            i += 1
            continue
        if line.startswith('```'):
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                if lines[i].strip():
                    covered(lines[i], 'equation_lines')
                i += 1
            require(i < len(lines), 'Unclosed equation fence')
        elif line.startswith('|'):
            cells = [value.strip() for value in line.strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', value) for value in cells):
                for cell in cells:
                    if cell:
                        covered(cell, 'table_cells')
        elif line.startswith('#'):
            covered(re.sub(r'^#{1,3}\s+', '', line), 'headings')
        else:
            block = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith(('#', '|', '```', '![')):
                i += 1
                block.append(lines[i].strip())
            covered(' '.join(block), 'paragraphs')
        i += 1
    require(counts['table_cells'] > 0 and counts['equation_lines'] >= 7,
            'Expected tables and mathematical illustrations')
    for ref in refs:
        require(normalized(ref['title']) in whole, 'Missing PDF reference: ' + ref['id'])
    for label in ['PHYSICAL VARIATION', 'REPRESENTATIONS', 'HELD-OUT TESTS',
                  'Negative controls: duplicate, shuffle, mask, drift, and break shortcuts']:
        require(normalized(label) in whole, 'Missing schematic label: ' + label)
    return counts


def verify_manifest():
    manifest = json.loads((ROOT / 'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    require(manifest['self_excluded'] is True, 'Manifest must exclude itself')
    require(manifest['version'] == '1.0.0', 'Unexpected release version')
    names = [row['path'] for row in manifest['files']]
    require(len(names) == len(set(names)), 'Duplicate manifest path')
    require(set(names) == ALLOWED_FILES, 'Release allowlist mismatch: '
            + repr(sorted(set(names) ^ ALLOWED_FILES)))
    for row in manifest['files']:
        name = row['path']
        path = PurePosixPath(name)
        require(not path.is_absolute() and '..' not in path.parts
                and path.as_posix() == name and '\\' not in name and ':' not in name,
                'Unsafe release path: ' + name)
        local = ROOT / name
        require(not local.is_symlink() and local.resolve().is_relative_to(ROOT),
                'Release file escapes package: ' + name)
        data = local.read_bytes()
        require(len(data) == row['bytes'], 'Size mismatch: ' + name)
        require(re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is not None, 'Invalid SHA-256: ' + name)
        require(hashlib.sha256(data).hexdigest() == row['sha256'], 'Hash mismatch: ' + name)
    return len(names)


def verify(rebuild=None):
    refs = json.loads((ROOT / 'references.json').read_text(encoding='utf-8-sig'))
    source = (ROOT / 'manuscript.md').read_text(encoding='utf-8-sig')
    readable = (ROOT / 'paper.md').read_text(encoding='utf-8-sig')
    unique = list(dict.fromkeys(re.findall(r'\[@([A-Z0-9]+)\]', source)))
    require(len(refs) == len(unique) == 49, 'Expected 49 declared sources')
    require(len({ref['id'] for ref in refs}) == len(refs), 'Duplicate source ID')
    require(set(unique) == {ref['id'] for ref in refs}, 'Reference mismatch')
    for ref in refs:
        require(all(ref.get(field) for field in ('id', 'authors', 'title', 'year',
                'publication', 'url', 'reading_scope', 'evidence_type', 'accessed')),
                'Incomplete reference metadata: ' + str(ref.get('id')))
        require(ref['url'].startswith('https://'), 'Non-HTTPS source: ' + ref['id'])
    require('[@' not in readable, 'Unresolved citations')
    vision = '## 9. Research vision proposed by AnimaFoundry'
    require(vision in source, 'Missing attributed vision')
    require(source.index(vision) < source.index('## Declarations'), 'Vision order')
    for scope in ['not a systematic review', 'All proposed physical and learning experiments remain unperformed.',
                  'Preprint. Not peer reviewed.', 'Internal AI-agent checks are not independent human peer review.']:
        require(scope in source, 'Missing scope limit: ' + scope)

    example_count = verify_examples(source)
    texts = pdf_text(ROOT / 'paper.pdf')
    coverage = verify_pdf_coverage(source, refs, unique, texts)
    manifest_count = verify_manifest()
    if rebuild:
        for name in ['paper.md', 'figures/crossmodal_loop.svg']:
            require((ROOT / name).read_bytes() == (rebuild / name).read_bytes(),
                    'Rebuild differs: ' + name)
        rebuilt = pdf_text(rebuild / 'paper.pdf')
        require(texts == rebuilt, 'Rebuilt PDF text or page boundaries differ')
    return {'status': 'PASS', 'sources': len(refs), 'pages': len(texts),
            'exact_examples': example_count, 'coverage': coverage,
            'manifest_files': manifest_count, 'rebuild_checked': bool(rebuild),
            'scope': 'document, manifest and exact arithmetic consistency; no empirical replication'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild', type=Path)
    try:
        print(json.dumps(verify(parser.parse_args().rebuild), indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
