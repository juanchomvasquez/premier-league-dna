"""AI-authored interpretation with cited, locally rendered numerical evidence.

Checks bound the format and citations; they do not verify prose semantics.
"""
from copy import deepcopy
import re


def calculated_profile_story(payload):
    """A factual, local explanation survives missing/rejected AI prose."""
    comparison=payload.get('illustrative_comparison') or {}
    candidates=comparison.get('candidates',[])
    spanish=payload.get('language')=='Spanish'
    if not candidates:
        if comparison.get('status')=='no_clear_profile':
            return 'Sin un perfil ilustrativo claro; eso no significa un mal rendimiento.' if spanish else 'No clear illustrative profile match; this does not mean poor performance.'
        return ''
    labels=[]
    for c in candidates:
        # Describe the two closest nonzero dimensions, not unsupported tactical reasons.
        axes=sorted([a for a in c['axes'] if a['observed_per_100_sequences']>0],key=lambda a:a['normalized_difference'])[:2]
        metrics=', '.join(a['metric'].lower() for a in axes)
        name=c['legend_label']
        if spanish:
            translations={'blocks':'bloqueos','successful take-ons':'regates completados','successful tackles':'entradas ganadas','interceptions':'intercepciones','aerial duels won':'duelos aéreos ganados','completed progressive passes':'pases completados hacia adelante','ball recoveries':'recuperaciones','shots':'remates','box arrivals':'llegadas al área','completed link-up passes':'pases de asociación completados','completed progressive carries':'conducciones progresivas completadas','completed switches':'cambios de orientación completados','saves':'paradas','successful claims':'balones aéreos atrapados','sweeper interventions':'intervenciones fuera del área','completed long distribution':'envíos largos completados','completed crosses':'centros completados','chances created':'ocasiones creadas','completed through balls':'pases al espacio completados','passes entering final third':'pases al último tercio','successful dribbles':'regates completados','touches in box':'toques en el área'}
            metrics=', '.join(translations.get(a['metric'].lower(),a['metric'].lower()) for a in axes)
            labels.append(f"perfil inspirado en {name.removesuffix('-inspired')}: mayor cercanía en {metrics}")
        else:labels.append(f"{name}: closest dimensions include {metrics}")
    prefix='Comparación ilustrativa con perfiles inventados. ' if spanish else 'Illustrative comparison with invented profiles. '
    suffix=' No es una semejanza histórica validada ni una mezcla porcentual.' if spanish else 'This is not validated historical similarity or a percentage blend.'
    return prefix+'; '.join(labels)+'.'+suffix

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
        if not headline.strip() or not narrative.strip():raise ValueError('Text required')
        text = headline+' '+narrative
        # Numbers are shown only in exact source facts below the interpretation.
        if re.search(r'[\d%<>{}\[\]]|https?://',text):raise ValueError('Prose must not introduce numerical claims or markup')
        if re.search(r'world.class|man of the match|\bbest\b|\bworst\b|\bdominat\w*|\bproved\b',text,re.I):
            raise ValueError('Unsupported overall assessment')
        if not isinstance(ids,list) or not 2 <= len(ids) <= 3 or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
            raise ValueError('Distinct citations required')
        index={e['id']:e for e in trusted['evidence']}
        facts=[index[i] for i in ids]
        evidence_edit=False
        if trusted.get('data_kind') == 'synthetic' and not any(e.get('kind')=='window_change' for e in facts):
            trend=re.compile(r'\b(recent|recently|increase[ds]?|decline[ds]?|surge|rose|fell|shift|late|reciente|aument[oó]|disminuy[oó]|baj[oó])\b',re.I)
            # Retain only the complete prefix: later sentences could depend on the rejected claim.
            kept=[]
            for sentence in re.split(r'(?<=[.!?])\s+',narrative.strip()):
                if trend.search(sentence):
                    evidence_edit=True;break
                kept.append(sentence)
            if evidence_edit:
                narrative=' '.join(kept)
                if not narrative.strip():raise ValueError('No supported text before trend')
                marker='sintétic' if trusted.get('language')=='Spanish' else 'synthetic'
                if marker not in narrative.casefold():
                    narrative=('Demostración sintética: ' if trusted.get('language')=='Spanish' else 'Synthetic demonstration: ')+narrative
            if trend.search(headline):
                headline='Participación del jugador' if trusted.get('language')=='Spanish' else 'Player contribution in focus'
                evidence_edit=True
            text=headline+' '+narrative
        if len({e['metric'] for e in facts}) < 2:raise ValueError('Multiple measurements required')
        if any(narrative.strip()==e['sentence'].strip() for e in facts):raise ValueError('A fact copy is not an interpretation')
        if trusted.get('data_kind')=='synthetic':
            marker='sintétic' if trusted.get('language')=='Spanish' else 'synthetic'
            if marker not in narrative.casefold():raise ValueError('Synthetic attribution required')
            candidates=trusted.get('illustrative_comparison',{}).get('candidates',[])
            allowed={c['legend_label'].removesuffix('-inspired').casefold():c['legend_label'] for c in candidates}
            mentioned=[name for name in trusted.get('excluded_legend_names',[]) if name.casefold() in text.casefold()]
            if any(name.casefold() not in allowed for name in mentioned):
                raise ValueError('No historical comparison in the synthetic brief')
            if mentioned:
                qualifier = r'inspirad' if trusted.get('language')=='Spanish' else r'-inspired'
                label = r'ilustrativ|inventad' if trusted.get('language')=='Spanish' else r'illustrative|invented'
                if not re.search(qualifier,narrative,re.I) or not re.search(label,narrative,re.I):
                    raise ValueError('Illustrative qualification required')
        if trusted.get('fit_status')!='candidate_mix':
            for name,r in trusted['references'].items():
                if name.casefold() in text.casefold() or r.get('short_label',name).casefold() in text.casefold():
                    raise ValueError('No legend resemblance is supported')
        return {'status':'evidence_checked','headline':headline.strip(),'text':narrative.strip(),
            'original_text':narrative.strip(),'shortened':False,
            'style_note':'Evidence edit: unsupported trend wording and any following continuation were omitted locally. No extra Microsoft request was made.' if evidence_edit else '',
            'facts':[e['sentence'] for e in facts], 'evidence_ids':ids,
            'illustrative_comparison':deepcopy(trusted.get('illustrative_comparison'))}
    except (ValueError,KeyError,TypeError) as error:
        # Only our own fixed validation labels are exposed, never provider text or unknown IDs.
        explanations = {
            'Unexpected structure':'The response did not use the required brief format.',
            'Text required':'The headline or brief was missing text.',
            'Prose must not introduce numerical claims or markup':'The prose included numbers or markup; exact figures belong in the supporting facts.',
            'Unsupported overall assessment':'The response included an unsupported overall player assessment.',
            'Distinct citations required':'The response did not cite two or three distinct supporting facts.',
            'No supported text before trend':'The response began with an unsupported trend claim, leaving no preceding text to show safely. The calculated style comparison remains available.',
            'A trend requires cited window-change evidence':'The response described a recent change without citing window-comparison evidence.',
            'Multiple measurements required':'The response did not cite different measurements.',
            'A fact copy is not an interpretation':'The response copied a supporting fact instead of explaining the pattern.',
            'Synthetic attribution required':'The brief did not identify the performance as synthetic.',
            'Illustrative qualification required':'The legend reference was not labelled as an invented or illustrative inspired profile.',
            'No historical comparison in the synthetic brief':'The response introduced an unsupported legend comparison.',
            'No legend resemblance is supported':'The response introduced an unsupported legend comparison.',
        }
        detail=explanations.get(str(error),'The response cited unavailable evidence or used an invalid format.') if isinstance(error,ValueError) else 'The response cited unavailable evidence or used an invalid format.'
        return {'status':'fallback','reason':detail+' No brief was accepted; recorded facts remain available.'}

