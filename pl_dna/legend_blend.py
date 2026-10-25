"""Descriptive mixtures of recorded match profiles; never career or ability scores."""
from copy import deepcopy
from itertools import combinations
import json
from pathlib import Path
import numpy as np

from pl_dna.recorded_events import METRICS

MIN_ACTIONS = 30  # Display floor, not a reliability guarantee.


def fit_blend(target, references, metric_keys=None):
    """Exact simplex least squares over every active face (two to four references).

    Equal squared error per rate point; no fitted scaling, softmax, or hand-set
    legend weights. Reject malformed inputs rather than substituting zeroes.
    """
    names, keys = list(references), list(METRICS if metric_keys is None else metric_keys)
    n = len(names)
    if not 2 <= n <= 4:
        raise ValueError('Two to four reference samples are required.')
    y = np.array([target['rates'][k] for k in keys], dtype=float)
    x = np.array([[references[n]['rates'][k] for n in names] for k in keys], dtype=float)
    if not np.isfinite(y).all() or not np.isfinite(x).all() or (y < 0).any() or (x < 0).any():
        raise ValueError('Rates must be finite nonnegative numbers.')
    if np.linalg.matrix_rank(np.vstack([x, np.ones(n)])) != n:
        raise ValueError('Reference profiles cannot distinguish a unique blend.')
    best = None
    for size in range(1, n+1):
        for active in combinations(range(n), size):
            a = x[:, active]
            system = np.block([[a.T @ a, np.ones((size, 1))],
                               [np.ones((1, size)), np.zeros((1, 1))]])
            solution = np.linalg.lstsq(system, np.r_[a.T @ y, 1.0], rcond=None)[0][:-1]
            if min(solution) < -1e-9:
                continue
            weights = np.zeros(n)
            weights[list(active)] = np.maximum(solution, 0)
            weights /= weights.sum()
            residual = float(np.mean((x @ weights - y)**2))
            if best is None or residual < best[0]:
                best = residual, weights
    residual, weights = best
    # Largest remainder display rounding: integer percentages total exactly 100.
    raw = 100 * weights
    percentages = np.floor(raw).astype(int)
    for i in sorted(range(n), key=lambda i: (-(raw[i] - percentages[i]), i))[:100-int(percentages.sum())]:
        percentages[i] += 1
    return dict(weights=dict(zip(names, weights.tolist())),
        percentages=dict(zip(names, percentages.tolist())),
        reconstructed_rates=dict(zip(keys, (x @ weights).tolist())),
        rmse=float(np.sqrt(residual)))


def build_blend_payload(study, target_key, minute, audience='Fan'):
    if type(minute) is not int or not 1 <= minute <= 90:
        raise ValueError('Choose an integer match minute from 1 to 90.')
    entry = study['targets'][target_key]
    target = deepcopy(entry['snapshots'][str(minute)])
    refs = deepcopy(study['references'])
    if any(entry['match_id'] in r['match_ids'] for r in refs.values()):
        raise ValueError('The selected match must not contribute to a reference sample.')
    payload = dict(task='legend_blend', version=1, target_key=target_key,
        player=entry['player'], match=study['fixtures'][str(entry['match_id'])], minute=minute,
        audience=audience, target=target, references=refs, coverage=study['coverage'],
        limitations=study['limitations'], availability='', evidence=[])
    if target['actions'] < MIN_ACTIONS:
        payload['availability'] = f"At least {MIN_ACTIONS} recorded passes, shots and dribbles are required to display this exploratory fit. Currently {target['actions']}."
        return payload
    fit = fit_blend(target, refs)
    payload['fit'] = fit
    ordered = sorted(refs, key=lambda n: -fit['weights'][n])
    # All metric comparisons are eligible editorial facts. AI cannot alter them.
    for name in ordered:
        for key, label in METRICS.items():
            selected, reference = target['rates'][key], refs[name]['rates'][key]
            direction = 'above' if selected > reference + 1e-8 else 'below' if selected < reference - 1e-8 else 'equal to'
            payload['evidence'].append(dict(id=f'{name}:{key}', legend=name, metric=key,
                label=label, count=target['counts'][key], actions=target['actions'],
                rate=selected, reference_rate=reference, direction=direction,
                sentence=f"{entry['player']} recorded {target['counts'][key]} {label.lower()} ({selected:.2f} per 100 on-ball actions), {direction} {name}’s recorded sample ({reference:.2f})."))
    # One-event sensitivity changes a qualifying count, keeping the observed
    # denominator fixed: an annotation sensitivity check, not a confidence interval.
    swings = []
    for key in METRICS:
        for delta in (-1, 1):
            if target['counts'][key] + delta < 0:
                continue
            altered = deepcopy(target)
            altered['rates'][key] += 100 * delta / target['actions']
            trial = fit_blend(altered, refs)
            swings.append(max(abs(trial['weights'][n] - fit['weights'][n])*100 for n in refs))
    payload['one_event_sensitivity_pp'] = max(swings)
    return payload


def validate_story(payload, candidate):
    if not isinstance(candidate, dict) or set(candidate) != {'angle', 'lead', 'support'}:
        raise ValueError('Expected an angle and two evidence IDs.')
    if candidate['angle'] not in ('closest_sample', 'mixed_profile', 'contrast'):
        raise ValueError('Unsupported story angle.')
    index = {e['id']: e for e in payload['evidence']}
    lead, support = candidate['lead'], candidate['support']
    if not isinstance(lead, str) or lead not in index:
        raise ValueError('Unsupported lead.')
    if support is not None and (not isinstance(support, str) or support not in index or support == lead):
        raise ValueError('Unsupported supporting evidence.')
    if candidate['angle'] == 'mixed_profile' and sum(v > .005 for v in payload['fit']['weights'].values()) < 2:
        raise ValueError('A mixed-profile story requires multiple nonzero weights.')
    return [deepcopy(index[k]) for k in (lead, support) if k is not None]


def story_text(payload, candidate):
    evidence = validate_story(payload, candidate)
    if payload.get('fit_status') == 'no_clear_match':
        return (f"No clear match to the loaded legend profiles for {payload['player']} under the current display checks. "
                'This is not an overall performance grade. ' + ' '.join(e['sentence'] for e in evidence))
    parts = [f"{pct}% {payload['references'][name].get('short_label', name.split()[-1])}" for name, pct in sorted(payload['fit']['percentages'].items(), key=lambda x: -x[1]) if pct]
    if payload.get('comparison_scope') == 'season_rates':
        summary = f"{payload['player']}’s recorded match rates fit {' / '.join(parts)} relative to the selected reference seasons. This is an exploratory comparison."
    else:
        summary = f"Through {payload['minute']} minutes, {payload['player']}’s recorded action mix fits {' / '.join(parts)} within these three match samples."
    return summary + ' ' + ' '.join(e['sentence'] for e in evidence)


def generate_blend_story(payload, provider):
    trusted = deepcopy(payload)
    if trusted['availability']:
        return dict(status='insufficient', reason=trusted['availability'])
    try:
        candidate = provider(deepcopy(trusted))
    except Exception as exc:
        from pl_dna.microsoft_provider import ProviderError
        code = exc.code if isinstance(exc, ProviderError) else 'provider_failure'
        safe = code if code in ('http_400', 'http_401', 'http_403', 'http_404', 'http_429', 'timeout', 'connection', 'incomplete_response', 'empty_response', 'invalid_json', 'invalid_response', 'refusal', 'oversized_response') else 'provider_failure'
        return dict(status='fallback', reason=f'Microsoft analysis unavailable ({safe}). The calculated blend remains available. No automatic retry was made.')
    try:
        text = story_text(trusted, candidate)
    except (ValueError, TypeError, KeyError):
        return dict(status='fallback', reason='Microsoft selected unsupported evidence. No AI story was accepted; the calculated blend remains available.')
    return dict(status='verified', text=text, selection=candidate)


def load_midfield_study():
    return json.loads((Path(__file__).parent/'data/midfield_study.json').read_text())
