"""Exact algebraic illustrations, not empirical sensor/model experiments.

All designs are hand-constructed here. No external dataset or random seed is used.
"""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rank(matrix):
    a = [[F(x) for x in row] for row in matrix]
    pivot = 0
    for col in range(len(a[0])):
        found = next((i for i in range(pivot, len(a)) if a[i][col]), None)
        if found is None:
            continue
        a[pivot], a[found] = a[found], a[pivot]
        scale = a[pivot][col]
        a[pivot] = [x / scale for x in a[pivot]]
        for i in range(len(a)):
            if i != pivot:
                scale = a[i][col]
                a[i] = [x - scale*y for x, y in zip(a[i], a[pivot])]
        pivot += 1
        if pivot == len(a):
            break
    return pivot


def prediction(x, theta):
    return [sum(F(v)*F(t) for v, t in zip(row, theta)) for row in x]


def describe(name, x, alternative=None):
    gram = [[sum(F(row[i])*F(row[j]) for row in x) for j in range(2)] for i in range(2)]
    y = prediction(x, (2, 3))
    result = {'name': name, 'rows': len(x), 'columns': 2, 'rank': rank(x),
              'gram': [[str(v) for v in row] for row in gram],
              'gram_determinant': str(gram[0][0]*gram[1][1] - gram[0][1]*gram[1][0]),
              'design': [[str(F(v)) for v in row] for row in x],
              'target': [str(v) for v in y]}
    if alternative is not None:
        result['alternative_theta'] = [str(F(v)) for v in alternative]
        result['indistinguishable_from_theta_2_3'] = prediction(x, alternative) == y
    return result


def calculate():
    silent = [(1, 0), (-1, 0), (1, 0), (-1, 0)]
    collinear = [(1, 1), (-1, -1), (1, 1), (-1, -1)]
    crossed = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    sparse = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    near = [(1, 1), (1, F(101, 100)), (-1, -1), (-1, F(-101, 100))]
    cases = [describe('silent_channel', silent, (2, 99)),
             describe('collinear_channels', collinear, (5, 0)),
             describe('crossed_variation', crossed),
             describe('sparse_but_spanning', sparse),
             describe('nearly_collinear', near)]
    repeated = describe('collinear_repeated_100_times', collinear*100, (5, 0))
    # Do not duplicate 400 rows in the output; retain an explicit construction.
    repeated.pop('design'); repeated.pop('target')
    repeated['construction'] = 'collinear_channels design repeated 100 times'
    cases.append(repeated)
    # At an exact fit, the loss gradient vanishes even though all parameters
    # are identifiable. Label noise cannot alter the design matrix rank.
    fitted = prediction(crossed, (2, 3))
    residual = [a-b for a,b in zip(fitted, prediction(crossed, (2, 3)))]
    gradient = [sum(F(row[j])*r for row,r in zip(crossed,residual)) for j in range(2)]
    return {'scope': 'exact hand-constructed linear algebra; no trained AI or physical measurements',
            'model': 'y = X theta, theta = (2,3), no intercept', 'cases': cases,
            'full_rank_exact_fit_gradient': [str(v) for v in gradient],
            'label_noise_changes_design_rank': False,
            'design_energy_matched': False,
            'warning': 'Rank does not establish causal identification, robustness or useful nonlinear representations.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    data = calculate()
    if args.write:
        (ROOT / 'identifiability_example.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({k:v for k,v in data.items() if k != 'cases'}, indent=2))
