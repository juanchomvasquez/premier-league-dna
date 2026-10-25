"""Current-match rates versus sourced, single-season historical references."""
from copy import deepcopy
import numpy as np
from pl_dna.legend_blend import fit_blend
from pl_dna.season_feed import FIELDS, ROLE_METRICS, ROLE_LABELS

# Provisional display checks, not calibrated statistical confidence thresholds.
# Large mismatch suppresses public mixture percentages; it never grades ability.
MAX_SCALED_RMSE = 0.5
MAX_AXIS_ERROR = 1.0

def _recorded_only(payload):
    """A missing legend comparison must not erase a usable match performance."""
    snapshot=payload['target'];minutes=snapshot['minutes']
    keys=[k for k in ROLE_METRICS[payload['role']] if snapshot['counts'].get(k) is not None and k not in snapshot['excluded_metrics']]
    payload['metric_keys']=keys
    payload['fit_status']='comparison_unavailable'
    payload['interpretation_available']=len(keys)>=2
    payload['evidence']=[dict(id='recorded:'+k,kind='recorded',legend=None,metric=k,label=FIELDS[k][0],
        sentence=f"{payload['player']} recorded {snapshot['counts'][k]:g} {FIELDS[k][0].lower()} in {minutes:g} minutes.") for k in keys]
    for label,fact in snapshot.get('execution',{}).items():
        payload['evidence'].append(dict(id='execution:'+label,kind='execution',legend=None,metric='execution:'+label,label=label,
            sentence=f"{payload['player']} — {label.lower()}: {fact['successful']:g} of {fact['attempted']:g} ({fact['percentage']:.1f}%) in {minutes:g} minutes."))
    return payload


def compare_season_player(player, snapshot, fixture, references, role):
    refs = {r['player']: deepcopy(r) for r in references if r['role'] == role}
    p = dict(task='legend_blend', comparison_scope='season_rates', version=2,
        player=player['name'], player_id=player['id'], role=role, role_label=ROLE_LABELS[role],
        target=deepcopy(snapshot), references=refs, fixture=deepcopy(fixture),
        minute=snapshot['minutes'], availability='', evidence=[],
        coverage='; '.join(f"{n} {r['season']} ({r['minutes']:g} PL minutes)" for n, r in refs.items()),
        limitations=['Historical coverage is identified for each reference: full selected seasons or explicitly labelled selected-match samples; never a hybrid of career-high metrics.',
            'Current match counts are from ESPN; historical counts come from the identified Premier League season service or StatsBomb Open Data match samples. Complete cross-provider equivalence has not been independently established.',
            'Weights are a descriptive, reference-scaled fit, not probabilities, ability ratings, or validated career-style similarity.',
            'Short-match per-90 rates can be volatile. Team role, opponent, game state and era are not adjusted for.',
            'Missing or disputed metrics are excluded; missing is never interpreted as zero.'],
        warnings=deepcopy(snapshot['warnings']))
    sample_refs=[r for r in refs.values() if r.get('reference_kind')=='match_sample']
    if sample_refs:
        p['comparison_scope']='match_sample_rates'
        p['reference_kind']='match_sample'
        p['limitations'].extend(sample_refs[0]['limitations'])
    minutes = snapshot['minutes']
    if minutes is None or minutes < 30:
        p['availability'] = 'At least 30 source-reported minutes are required for this exploratory comparison. This display floor is not a reliability guarantee.'
        return p
    if not 2 <= len(refs) <= 4:
        p['availability'] = 'At least two usable historical references are needed for this position.'
        return _recorded_only(p)
    keys = [k for k in ROLE_METRICS[role] if k not in snapshot['excluded_metrics']
        and snapshot['counts'][k] is not None and all(r['counts'][k] is not None for r in refs.values())]
    reference_rates = {n: {k: 90*r['counts'][k]/r['minutes'] for k in keys} for n, r in refs.items()}
    scales = {k: max(reference_rates[n][k] for n in refs) for k in keys}
    keys = [k for k in keys if scales[k] > 0]
    if len(keys) < 3:
        p['availability'] = 'Fewer than three usable shared metrics remain. The recorded counts are available; no blend is calculated.'
        return _recorded_only(p)
    target_rates = {k: 90*snapshot['counts'][k]/minutes for k in keys}
    scaled_refs = {n: {'rates': {k: reference_rates[n][k]/scales[k] for k in keys}} for n in refs}
    try:
        fit = fit_blend({'rates': {k: target_rates[k]/scales[k] for k in keys}}, scaled_refs, keys)
    except ValueError:
        p['availability'] = 'These shared metrics cannot identify a unique blend from the loaded references.'
        return _recorded_only(p)
    p.update(fit=fit, metric_keys=keys, target_rates=target_rates, reference_rates=reference_rates,
             scales={k: scales[k] for k in keys}, omitted_metrics=[k for k in ROLE_METRICS[role] if k not in keys],
             fitted_rates={k: fit['reconstructed_rates'][k]*scales[k] for k in keys})
    largest_error = max(abs(target_rates[k]/scales[k]-fit['reconstructed_rates'][k]) for k in keys)
    supported = fit['rmse'] <= MAX_SCALED_RMSE and largest_error <= MAX_AXIS_ERROR
    p['fit_status'] = 'candidate_mix' if supported else 'no_clear_match'
    p['fit_checks'] = {'scaled_rmse': fit['rmse'], 'maximum_axis_error': largest_error,
        'rmse_display_limit': MAX_SCALED_RMSE, 'axis_display_limit': MAX_AXIS_ERROR,
        'interpretation': 'Provisional display policy, not validated confidence. Weak fits hide blend percentages. A mismatch is not a poor-performance grade.'}
    for name, r in refs.items():
        r['short_label'] = r['inspiration'].removesuffix('-inspired')
        for k in keys:
            label = FIELDS[k][0]
            actual, reference = target_rates[k], reference_rates[name][k]
            direction = 'above' if actual > reference + 1e-8 else 'below' if actual < reference - 1e-8 else 'equal to'
            p['evidence'].append(dict(id=f'{name}:{k}', legend=name, metric=k, label=label,
                count=snapshot['counts'][k], minutes=minutes, rate=actual, reference_rate=reference,
                direction=direction,
                sentence=f"{player['name']} recorded {snapshot['counts'][k]:g} {label.lower()} in {minutes:g} minutes ({actual:.2f} per 90), {direction} {name}’s {r['season']} PL rate ({reference:.2f} per 90)."))
    # Numerical reproducibility check independent of the scaled residual display.
    reconstruction = np.array([sum(fit['weights'][n]*reference_rates[n][k] for n in refs) for k in keys])
    if not np.allclose(reconstruction, list(p['fitted_rates'].values()), atol=1e-8):
        raise ValueError('Mixture reconstruction failed.')
    # Outcome evidence can explain execution without asserting a legend match.
    # These facts do not enter the style fit or imply a benchmark/overall grade.
    for label, fact in snapshot.get('execution', {}).items():
        p['evidence'].append(dict(id='execution:'+label, kind='execution',
            legend=None, metric='execution:'+label, label=label,
            sentence=f"{player['name']} — {label.lower()}: {fact['successful']:g} of {fact['attempted']:g} ({fact['percentage']:.1f}%) in {minutes:g} minutes."))
    return p
