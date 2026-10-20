"""Grounded narrative selection and deterministic rendering.

An optional provider selects and orders structured claims. It cannot supply
prose, explanations, scores, or causal claims. No network calls occur here.
Validation verifies consistency with the supplied evidence payload; it does not
independently establish that the underlying synthetic events are realistic.
"""
from __future__ import annotations
from copy import deepcopy
from collections.abc import Callable

CLAIM_KEYS = {"measurement", "count", "event_ids", "supporting_event_ids"}
SPANISH_METRICS = {
    "Successful tackles": "entradas ganadas", "Interceptions": "intercepciones",
    "Aerial duels won": "duelos aéreos ganados", "Blocks": "bloqueos",
    "Completed progressive passes": "pases progresivos completados",
    "Completed crosses": "centros completados",
    "Completed progressive carries": "conducciones progresivas completadas",
    "Chances created": "ocasiones creadas", "Box arrivals": "llegadas al área",
    "Shots": "remates", "Completed switches": "cambios de orientación completados",
    "Successful take-ons": "regates exitosos", "Completed link-up passes": "pases de apoyo completados",
    "Ball recoveries": "recuperaciones de balón",
    "Saves": "paradas", "Successful claims": "balones atrapados con éxito",
    "Sweeper interventions": "intervenciones fuera del área",
    "Completed long distribution": "envíos largos completados",
    "Completed through balls": "pases filtrados completados",
    "Passes entering final third": "pases que entran en el último tercio",
}


def _ids(value, field):
    if not isinstance(value,list) or any(not isinstance(x,str) for x in value):
        raise ValueError(f"{field} must be a list of event IDs.")
    if len(value)!=len(set(value)):
        raise ValueError(f"{field} contains duplicate IDs.")
    return value


def _evidence_index(payload):
    try:
        measurements=payload["evidence"]["measurements"]
    except (KeyError,TypeError):
        raise ValueError("Payload has no measurement evidence.") from None
    if not isinstance(measurements,list):
        raise ValueError("Measurements must be a list.")
    indexed={}
    for m in measurements:
        if not isinstance(m,dict) or not isinstance(m.get("measurement"),str):
            raise ValueError("Malformed measurement evidence.")
        name=m["measurement"]
        count=m.get("count")
        if name in indexed or type(count) is not int or count<0:
            raise ValueError("Evidence has duplicate measurements or invalid counts.")
        ids=_ids(m.get("event_ids"),"event_ids")
        secondary=_ids(m.get("supporting_event_ids",[]),"supporting_event_ids")
        if count!=len(ids):
            raise ValueError("Evidence count does not match its event IDs.")
        indexed[name]={"measurement":name,"count":count,"event_ids":list(ids),"supporting_event_ids":list(secondary)}
    return indexed


def validate_candidate(payload, candidate):
    """Validate up to3 exact evidence claims; reject all free-form additions.

    Claim ordering and evidence ID ordering may change; no evidence may be
    omitted, duplicated, or added within a selected measurement.
    """
    evidence=_evidence_index(payload)
    if not isinstance(candidate,dict) or set(candidate)!={"claims"}:
        raise ValueError("Candidate must contain only structured claims.")
    claims=candidate["claims"]
    if not isinstance(claims,list) or not 1<=len(claims)<=3:
        raise ValueError("Select between one and three claims.")
    seen=set();result=[]
    for claim in claims:
        if not isinstance(claim,dict) or set(claim)!=CLAIM_KEYS:
            raise ValueError("Each claim must use the exact evidence schema.")
        name=claim["measurement"]
        if not isinstance(name,str) or name not in evidence or name in seen:
            raise ValueError("Claim measurement is unknown or duplicated.")
        expected=evidence[name]
        if type(claim["count"]) is not int or claim["count"]!=expected["count"]:
            raise ValueError("Claim count disagrees with evidence.")
        for field in ("event_ids","supporting_event_ids"):
            actual=_ids(claim[field],field)
            if set(actual)!=set(expected[field]):
                raise ValueError("Claim event IDs disagree with evidence.")
        seen.add(name);result.append(deepcopy(expected))
    return result


def _fallback_claims(payload):
    values=list(_evidence_index(payload).values())
    positive=[m for m in values if m["count"]>0]
    return deepcopy((positive or values)[:3])


def _render(payload,claims,language):
    player=payload.get("player","Selected player")
    window=payload.get("window",{})
    start=window.get("start_exclusive",payload["evidence"].get("start_minute_exclusive",0))
    end=window.get("end_inclusive",payload["evidence"].get("end_minute_inclusive",90))
    if not claims:
        if language=="Spanish":
            return f"{player}, minutos ({start}, {end}]: no se proporcionaron mediciones registradas. Demostración sintética."
        return f"{player}, minutes ({start}, {end}]: no recorded measurements were supplied. Synthetic demonstration."
    if language=="Spanish":
        facts=[f"{c['count']} {SPANISH_METRICS.get(c['measurement'],c['measurement'].lower())}" if c['count'] else f"sin eventos registrados de {SPANISH_METRICS.get(c['measurement'],c['measurement'].lower())}" for c in claims]
        return f"{player}, minutos ({start}, {end}]: " + "; ".join(facts) + ". Demostración sintética. Las mediciones pueden coincidir en una misma secuencia."
    facts=[f"{c['count']} {c['measurement'].lower()}" if c['count'] else f"no recorded events for {c['measurement'].lower()}" for c in claims]
    return f"{player}, minutes ({start}, {end}]: " + "; ".join(facts) + ". Synthetic demonstration. Measurements can overlap within the same sequence."


def generate_narrative(payload, provider: Callable | None=None, language="English"):
    """Return text and transparent provenance, with safe deterministic fallback.

    provider receives a deep copy of payload and returns {"claims": [claim,...]}.
    Provider failure or invalid selections never reach the text renderer.
    "verified" means model selections match evidence, not model prose approval.
    "fallback" explicitly indicates deterministic selection without accepted AI.
    """
    if language not in ("English","Spanish"):
        raise ValueError("Supported languages are English and Spanish.")
    trusted=deepcopy(payload)
    claims=_fallback_claims(trusted)
    status="fallback";source="deterministic";reason="No model provider configured."
    if provider is not None:
        try:
            candidate=provider(deepcopy(trusted))
        except Exception:
            reason="Model provider failed; used deterministic evidence selection."
        else:
            try:
                claims=validate_candidate(trusted,candidate)
            except (ValueError,TypeError,KeyError):
                reason="Model selection failed evidence validation; used deterministic evidence selection."
            else:
                status="verified";source="model-selected";reason="Structured model selections match supplied evidence."
    return {"text":_render(trusted,claims,language),"status":status,"reason":reason,
            "claims":claims,"source":source}
