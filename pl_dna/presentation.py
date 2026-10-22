"""Escaped display components; no measurements or model calls."""
from html import escape

AUDIENCES = {
    "Fan": "The story first. Explore the actions behind the profile.",
    "Broadcaster": "A concise talking point, with the facts ready to check.",
    "Expert": "Inspect counts, rates, model assumptions and event evidence.",
}
ROLE_AREAS = {"GK": (12, 50), "CB": (28, 50), "FB": (37, 16), "CDM": (44, 50),
              "CM": (56, 50), "CAM": (70, 50), "WING": (76, 16), "ST": (88, 50)}


def player_header(player, role, role_label, start, end, view):
    """Position guide is schematic, never a measured location or heatmap."""
    x, y = ROLE_AREAS[role]
    return f"""<section class="player-hero" aria-label="Selected player">
      <div><div class="eyebrow">PLAYER SPOTLIGHT · {escape(role)}</div>
      <h2>{escape(player)}</h2><p>{escape(role_label)} · {escape(view)} · minutes ({start}, {end}]</p>
      <div class="hero-tag">FICTIONAL PLAYER / SYNTHETIC EVENTS</div></div>
      <figure class="position-pitch">
      <svg viewBox="0 0 120 80" role="img" aria-label="Schematic {escape(role_label)} position; not tracking data">
        <rect x="4" y="4" width="112" height="72" rx="3" fill="#10352f" stroke="#69ad9c"/>
        <path d="M60 4v72 M4 22h17v36H4 M116 22H99v36h17" fill="none" stroke="#69ad9c"/>
        <circle cx="60" cy="40" r="12" fill="none" stroke="#69ad9c"/>
        <circle cx="{4+x*1.12}" cy="{4+y*.72}" r="10" fill="#39dfbc" fill-opacity=".18"/>
        <circle cx="{4+x*1.12}" cy="{4+y*.72}" r="4" fill="#39dfbc" stroke="#fff"/>
      </svg><figcaption>Position guide · schematic</figcaption></figure>
    </section>"""


def profile_cards(definition, scores):
    cards = []
    for profile in definition["profiles"]:
        name = definition.get("legend_inspirations", {}).get(profile, profile)
        score = scores.get(profile)
        if score is None:
            value = '<div class="profile-score muted">Insufficient sample</div>'
            bar = '<div class="score-track" aria-hidden="true"></div>'
        else:
            value = f'<div class="profile-score">{score:.1f}<small> / 100</small></div>'
            bar = (f'<div class="score-track" role="meter" aria-label="{escape(name)} model score" '
                   f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{score:.1f}">'
                   f'<div class="score-fill" style="width:{max(0,min(100,score)):.1f}%"></div></div>')
        cards.append(f'<article class="profile-card"><div class="eyebrow">INVENTED PROFILE</div>'
                     f'<h4>{escape(name)}</h4><p>{escape(profile)}</p>{value}{bar}</article>')
    return '<div class="profile-grid">' + ''.join(cards) + '</div>'


def insight_card(text, audience):
    title = {"Fan": "The match story", "Broadcaster": "Talking point", "Expert": "Evidence-grounded summary"}[audience]
    return (f'<section class="insight-card"><div class="eyebrow">{title.upper()}</div>'
            f'<p>{escape(text)}</p></section>')
