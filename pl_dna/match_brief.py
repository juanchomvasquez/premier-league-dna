"""Evidence-backed match-development briefs; no inferred tactics or ability scores."""
from copy import deepcopy
from pl_dna.roles import analyze_role_player, ROLE_DEFINITIONS
from pl_dna.narrative import SPANISH_METRICS

CONTEXT = {
    'Shots': ('Shooting involvement', 'Attempts show shooting involvement, not shot quality or finishing ability.', 'Does shooting involvement continue in the next window?'),
    'Box arrivals': ('Penalty-area involvement', 'Arrivals record movement into the box; they do not establish that a chance was created.', 'Do box arrivals continue alongside shooting involvement?'),
    'Chances created': ('Chance creation', 'These are completed key passes supported by a teammate shot in the same recorded sequence.', 'Does the player keep supplying teammates with shots?'),
    'Completed progressive passes': ('Ball progression by passing', 'Completed progressive passes record forward ball movement; they do not establish territorial control.', 'Does progression by passing continue?'),
    'Completed progressive carries': ('Ball progression by carrying', 'Progressive carries record forward movement with the ball, not the cause of that movement.', 'Does the player continue advancing the ball by carrying?'),
    'Completed switches': ('Distribution across the pitch', 'Completed switches record changes of play across the pitch; they do not prove a tactical change.', 'Does switching play remain part of the recorded contribution?'),
    'Completed crosses': ('Wide delivery', 'Completed crosses record wide delivery, not the quality of the resulting chance.', 'Do wide deliveries lead to recorded chances in the next window?'),
    'Completed through balls': ('Penetrative passing', 'Through balls record a specific passing contribution, not an overall creativity rating.', 'Does penetrative passing continue?'),
    'Passes entering final third': ('Passing into the final third', 'These passes show ball progression into the final third; they do not establish possession dominance.', 'Does final-third entry by passing continue?'),
    'Completed link-up passes': ('Link-up involvement', 'Link-up passes record connections with teammates, not an overall attacking rating.', 'Does link-up involvement continue alongside box arrivals?'),
    'Successful take-ons': ('One-on-one contribution', 'Successful take-ons record won dribbles; they do not establish an overall dribbling ability.', 'Does one-on-one involvement continue?'),
    'Successful tackles': ('Tackling contribution', 'Won tackles record successful interventions; fewer tackles do not by themselves mean worse defending.', 'How does tackling involvement develop alongside interceptions?'),
    'Interceptions': ('Interception contribution', 'Interceptions record retained ball recoveries from passes, not an overall defensive rating.', 'Do interceptions continue alongside the other defensive actions?'),
    'Ball recoveries': ('Recovery contribution', 'Recoveries record regaining the ball; they do not establish pressing intensity or its cause.', 'Does recovery involvement continue?'),
    'Aerial duels won': ('Aerial contribution', 'Won aerial duels record successful contests; attempts and win percentage are not supplied.', 'Do won aerial contests remain part of the contribution?'),
    'Blocks': ('Blocking contribution', 'Blocks record interventions; a higher count is not automatically better overall defending.', 'Do blocking interventions continue in the next window?'),
    'Saves': ('Shot-stopping workload', 'Saves are supported by opposing shots; save percentage and shot difficulty are not supplied.', 'Does the recorded save workload continue?'),
    'Successful claims': ('Goalkeeper claims', 'Claims record successful collections, not overall command of the penalty area.', 'Do successful collections continue?'),
    'Sweeper interventions': ('Goalkeeper interventions outside the area', 'These interventions record activity outside the area; they do not prove a high defensive line.', 'Does intervention outside the area continue?'),
    'Completed long distribution': ('Goalkeeper distribution', 'Completed long distribution records successful long deliveries; pass attempts are not supplied.', 'Does long distribution remain part of the contribution?'),
}


def build_match_brief(data, player, end):
    """Compare adjacent, nonoverlapping 15-minute windows, both censored at their ends."""
    payload = {'task': 'match_development', 'player': player, 'end': end,
               'comparisons': [], 'availability': '', 'data_type': 'synthetic demonstration'}
    if end < 30:
        payload['availability'] = 'Two complete 15-minute windows are needed. Move the match minute to 30 or later.'
        return payload
    previous = analyze_role_player(data, player, end - 30, end - 15)
    recent = analyze_role_player(data, player, end - 15, end)
    payload.update(role=recent['role'], role_label=ROLE_DEFINITIONS[recent['role']]['label'],
                   previous=previous, recent=recent)
    if min(previous['action_sequences'], recent['action_sequences']) < 3:
        payload['availability'] = 'Too few recorded sequences in one of the windows to highlight a change.'
        return payload
    for i, (before, after) in enumerate(zip(previous['measurements'], recent['measurements'], strict=True)):
        if before['measurement'] != after['measurement']:
            raise ValueError('Window measurements do not align.')
        # Avoid a headline based on a single isolated event. This is an editorial
        # threshold, not a statistical significance or performance-quality test.
        if before['count'] == after['count'] or before['count'] + after['count'] < 3:
            continue
        metric = after['measurement']
        title, meaning, watch = CONTEXT[metric]
        payload['comparisons'].append(dict(id=f'change_{i}', measurement=metric,
            before=deepcopy(before), after=deepcopy(after),
            direction='increased' if after['count'] > before['count'] else 'decreased',
            topic=title, meaning=meaning, watch=watch))
    if not payload['comparisons']:
        payload['availability'] = 'No count changes meet the minimum evidence threshold in these two windows. There is no supported change to highlight.'
    return payload


def validate_brief(payload, candidate):
    """AI picks a lead and optional contrasting/supporting change, never invents facts."""
    if not isinstance(candidate, dict) or set(candidate) != {'lead', 'support'}:
        raise ValueError('Expected a lead and an optional support ID.')
    indexed = {c['id']: c for c in payload['comparisons']}
    lead, support = candidate['lead'], candidate['support']
    if not isinstance(lead, str) or lead not in indexed:
        raise ValueError('Unknown lead evidence.')
    if support is not None and (not isinstance(support, str) or support not in indexed or support == lead):
        raise ValueError('Unknown or repeated supporting evidence.')
    return deepcopy([indexed[k] for k in (lead, support) if k is not None])


def render_brief(payload, selected, language):
    spanish = language == 'Spanish'
    start, split, end = payload['end'] - 30, payload['end'] - 15, payload['end']
    facts = []
    for c in selected:
        metric = SPANISH_METRICS.get(c['measurement'], c['measurement']) if spanish else c['measurement'].lower()
        direction = ('aumentaron' if c['direction'] == 'increased' else 'disminuyeron') if spanish else c['direction']
        facts.append(f"{metric}: {c['before']['count']} → {c['after']['count']} ({direction})")
    headline = f"{selected[0]['topic']} {selected[0]['direction']}"
    if len(selected) > 1:
        join = ' while ' if selected[0]['direction'] != selected[1]['direction'] else ' and '
        headline += join + f"{selected[1]['topic'].lower()} {selected[1]['direction']}"
    headline += '.'
    period = f'({start}, {split}] → ({split}, {end}]'
    return dict(headline=headline, facts=facts, period=period,
                meaning=[c['meaning'] for c in selected], watch=selected[0]['watch'],
                evidence=selected,
                caution='Dos periodos breves de eventos sintéticos. Los cambios en recuentos no demuestran mejores resultados ni explican su causa.' if spanish else
                'Two short windows of synthetic events. Count changes do not establish better performance or explain their cause.')


def generate_match_brief(payload, provider=None, language='English'):
    trusted = deepcopy(payload)
    if trusted['availability']:
        return dict(status='insufficient', reason=trusted['availability'], brief=None)
    if provider is None:
        return dict(status='preview', reason='Click Generate match analysis to ask Microsoft AI to select a supported development.', brief=None)
    try:
        selected = validate_brief(trusted, provider(deepcopy(trusted)))
    except Exception:
        return dict(status='fallback', reason='Microsoft analysis was unavailable or returned unsupported evidence. No AI brief was accepted.', brief=None)
    return dict(status='verified', reason='AI-selected developments match the calculated window comparisons.',
                brief=render_brief(trusted, selected, language))
