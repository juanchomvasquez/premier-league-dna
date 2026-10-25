"""Escaped display components; no measurements or model calls."""
from html import escape

AUDIENCES = {
    "Fan": "The story first. Explore the actions behind the profile.",
    "Broadcaster": "A concise talking point, with the facts ready to check.",
    "Expert": "Inspect counts, rates, model assumptions and event evidence.",
}
ROLE_AREAS = {"GK": (12, 50), "CB": (28, 50), "FB": (37, 16), "CDM": (44, 50),
              "CM": (56, 50), "CAM": (70, 50), "WING": (76, 16), "ST": (88, 50)}

# Selected club-era inspirations, not claims of an exclusive or current club.
# Approximate club-inspired accents; dark tints preserve readable card text.
CLUB_COLOURS = {
    "Everton": ("#1455d9", "#13274a"),
    "Tottenham Hotspur": ("#f4f5f7", "#1b2443"),
    "Chelsea": ("#2463eb", "#142b52"),
    "Arsenal": ("#ef3340", "#3d202e"),
    "Manchester United": ("#da291c", "#3c222d"),
    "Liverpool": ("#c8102e", "#3c2030"),
    "Manchester City": ("#6cabdd", "#183548"),
    "Newcastle United": ("#e5e7eb", "#282d37"),
}
LEGEND_CLUBS = {
    "Schmeichel-inspired": "Manchester United",
    "Cech-inspired": "Chelsea", "Alisson-inspired": "Liverpool",
    "Terry-inspired": "Chelsea", "Vidic-inspired": "Manchester United",
    "Van Dijk-inspired": "Liverpool", "Ashley Cole-inspired": "Chelsea",
    "Kyle Walker-inspired": "Manchester City",
    "Alexander-Arnold-inspired": "Liverpool", "Makelele-inspired": "Chelsea",
    "Kante-inspired": "Chelsea", "Rodri-inspired": "Manchester City",
    "Lampard-inspired": "Chelsea", "Gerrard-inspired": "Liverpool",
    "Scholes-inspired": "Manchester United", "Ozil-inspired": "Arsenal",
    "De Bruyne-inspired": "Manchester City", "Fabregas-inspired": "Chelsea",
    "Ronaldo-inspired": "Manchester United", "Hazard-inspired": "Chelsea",
    "Salah-inspired": "Liverpool", "Shearer-inspired": "Newcastle United",
    "Drogba-inspired": "Chelsea", "Henry-inspired": "Arsenal",
    "Rooney-inspired": "Manchester United",
}


def player_header(player, role, role_label, start, end, view):
    """Position guide is schematic, never a measured location or heatmap."""
    x, y = ROLE_AREAS[role]
    return f"""<section class="player-hero" aria-label="Selected player">
      <div><div class="eyebrow">PLAYER SPOTLIGHT · {escape(role)}</div>
      <h2>{escape(player)}</h2><p>{escape(role_label)} · {escape(view)} · minutes ({start}, {end}]</p>
      <div class="hero-tag">FICTIONAL PLAYER / SYNTHETIC EVENTS</div></div>
      <figure class="position-pitch">
      <div role="img" aria-label="Schematic {escape(role_label)} position; not tracking data"
           style="position:relative;width:100%;aspect-ratio:112/72;background:#10352f;border:1px solid #69ad9c;border-radius:4px;overflow:hidden;">
        <span style="position:absolute;left:50%;top:0;height:100%;border-left:1px solid #69ad9c;"></span>
        <span style="position:absolute;left:39%;top:33%;width:22%;height:34%;border:1px solid #69ad9c;border-radius:50%;"></span>
        <span style="position:absolute;left:0;top:25%;width:15%;height:50%;border:1px solid #69ad9c;border-left:0;"></span>
        <span style="position:absolute;right:0;top:25%;width:15%;height:50%;border:1px solid #69ad9c;border-right:0;"></span>
        <span style="position:absolute;left:{x}%;top:{y}%;width:11px;height:11px;transform:translate(-50%,-50%);background:#00ff85;border:2px solid white;border-radius:50%;box-shadow:0 0 0 8px #00ff8530;"></span>
      </div><figcaption>Position guide · schematic</figcaption></figure>
    </section>"""


def profile_cards(definition, scores, show_scores=True):
    cards = []
    for profile in definition["profiles"]:
        name = definition.get("legend_inspirations", {}).get(profile, profile)
        club = LEGEND_CLUBS.get(name)
        accent, tint = CLUB_COLOURS[club] if club else ("#b69aff", "#221c36")
        club_label = (f'<div style="font-size:.72rem;color:#d1deed;margin:8px 0 12px;">'
                      f'{escape(club)} · club inspiration</div>') if club else ""
        score = scores.get(profile)
        if not show_scores:
            value = '<div class="profile-score muted">Historical calibration pending</div>'
            bar = ''
        elif score is None:
            value = '<div class="profile-score muted">Insufficient sample</div>'
            bar = '<div class="score-track" aria-hidden="true"></div>'
        else:
            value = f'<div class="profile-score">{score:.1f}<small> / 100</small></div>'
            bar = (f'<div class="score-track" role="meter" aria-label="{escape(name)} model score" '
                   f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{score:.1f}">'
                   f'<div class="score-fill" style="width:{max(0,min(100,score)):.1f}%"></div></div>')
        cards.append(f'<article class="profile-card" style="border-top:4px solid {accent};'
                     f'background:linear-gradient(145deg,{tint},#321044);">'
                     f'<div class="eyebrow">INVENTED PROFILE</div>'
                     f'<h4>{escape(name)}</h4>{club_label}<p>{escape(profile)}</p>{value}{bar}</article>')
    return '<div class="profile-grid">' + ''.join(cards) + '</div>'


def insight_card(text, audience):
    title = {"Fan": "The match story", "Broadcaster": "Talking point", "Expert": "Evidence-grounded summary"}[audience]
    return (f'<section class="insight-card"><div class="eyebrow">{title.upper()}</div>'
            f'<p>{escape(text)}</p></section>')


# The public legend pool contains retired players only.
from pl_dna.retired_roster import REPLACEMENTS, records as retired_records
for _old in REPLACEMENTS: LEGEND_CLUBS.pop(_old, None)
LEGEND_CLUBS.update({name:r['club'] for name,r in retired_records().items()})
