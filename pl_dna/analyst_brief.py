"""AI-authored interpretation with cited, locally rendered numerical evidence.

Checks bound the format and citations; they do not verify prose semantics.
"""
from copy import deepcopy
import re


def generate_analyst_brief(payload, provider):
    trusted = deepcopy(payload)
    if trusted['availability'] and not trusted.get('interpretation_available'):
        return {'status':'insufficient','reason':trusted['availability']}
    request = deepcopy(trusted)
    request['task'] = 'performance_interpretation'
    try:
        reply = provider(request)
    except Exception:
        return {'status':'fallback','reason':'Microsoft interpretation is unavailable. Recorded facts remain available; no automatic retry was made.'}
    try:
        if not isinstance(reply,dict) or set(reply)!={'headline','narrative','evidence_ids'}:
            raise ValueError('Unexpected structure')
        headline,narrative,ids = reply['headline'],reply['narrative'],reply['evidence_ids']
        if not isinstance(headline,str) or not isinstance(narrative,str):raise ValueError('Text required')
        if not 3 <= len(headline.split()) <= 14 or not 20 <= len(narrative.split()) <= 110:
            raise ValueError('Length')
        text = headline+' '+narrative
        # Numbers are shown only in exact source facts below the interpretation.
        if re.search(r'[\d%<>{}\[\]]|https?://',text):raise ValueError('Prose must not introduce numerical claims or markup')
        if re.search(r'world.class|man of the match|\bbest\b|\bworst\b|\bdominat\w*|\bproved\b',text,re.I):
            raise ValueError('Unsupported overall assessment')
        if not isinstance(ids,list) or not 2 <= len(ids) <= 3 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
            raise ValueError('Distinct citations required')
        index={e['id']:e for e in trusted['evidence']}
        facts=[index[i] for i in ids]
        if len({e['metric'] for e in facts}) < 2:raise ValueError('Multiple measurements required')
        if any(narrative.strip()==e['sentence'].strip() for e in facts):raise ValueError('A fact copy is not an interpretation')
        if trusted.get('fit_status')!='candidate_mix':
            for name,r in trusted['references'].items():
                if name.casefold() in text.casefold() or r.get('short_label',name).casefold() in text.casefold():
                    raise ValueError('No legend resemblance is supported')
        return {'status':'evidence_checked','headline':headline.strip(),'text':narrative.strip(),
            'facts':[e['sentence'] for e in facts], 'evidence_ids':ids}
    except (ValueError,KeyError,TypeError):
        return {'status':'fallback','reason':'Microsoft returned an interpretation that failed the format or evidence checks. No brief was accepted; recorded facts remain available.'}
