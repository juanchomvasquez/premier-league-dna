"""DNA visual preview. Uses actual metric rates, never invented ability ratings."""
from html import escape
import math
import textwrap


SHORT_LABELS = {
    "Completed progressive passes": "Progressive passes",
    "Completed progressive carries": "Progressive carries",
    "Completed switches": "Switches",
    "Completed through balls": "Through balls",
    "Completed crosses": "Crosses",
    "Completed link-up passes": "Link-up passes",
    "Completed long distribution": "Long distribution",
    "Passes entering final third": "Final-third entries",
}


def wheel_data(definition, report, profile):
    """Retain exact counts and rates for the chart and accessible table.

    All axes share the same unit: counts per 100 recorded sequences. References
    are the existing illustrative fixtures; no historical season is assigned.
    """
    count = report["action_sequences"]
    observed = {item["measurement"]: item["count"] for item in report["measurements"]}
    return [dict(measurement=label, count=observed[label],
                 observed_rate=100 * observed[label] / count if count else None,
                 reference_rate=float(reference))
            for label, reference in zip(definition["metrics"], definition["profiles"][profile], strict=True)]


def radar_svg(rows, player, reference_name, show_observed=True, scale_max=100):
    """Self-contained SVG served as an image so HTML sanitizers cannot strip it."""
    if len(rows) < 3:
        raise ValueError("A wheel requires at least three metrics.")
    values = [row["reference_rate"] for row in rows]
    values += [row["observed_rate"] for row in rows if row["observed_rate"] is not None]
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Wheel rates must be finite and nonnegative.")
    # Keep the role's baseline fixed across references; expand, never clip overflow.
    if not math.isfinite(scale_max) or scale_max <= 0:
        raise ValueError("The wheel scale must be finite and positive.")
    maximum = max(scale_max, math.ceil(max(values, default=0) / 20) * 20)
    cx, cy, radius = 320, 230, 145
    angles = [-math.pi / 2 + i * 2 * math.pi / len(rows) for i in range(len(rows))]

    def point(angle, amount):
        return cx + math.cos(angle) * amount, cy + math.sin(angle) * amount

    def polygon(rates):
        return " ".join(f"{x:.2f},{y:.2f}" for angle, rate in zip(angles, rates, strict=True)
                        for x, y in [point(angle, radius * rate / maximum)])

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 470" role="img" '
             f'aria-labelledby="dna-title dna-desc"><title id="dna-title">Player DNA wheel</title>'
             f'<desc id="dna-desc">{escape(player)} versus {escape(reference_name)}. '
             'Illustrative reference, not historical statistics. All axes are rates per 100 recorded sequences.</desc>',
             '<rect width="640" height="470" rx="20" fill="#321044"/>',
             '<text x="28" y="32" fill="#9eabc5" font-family="Arial,sans-serif" font-size="11" letter-spacing="2">PERFORMANCE SHAPE / DESIGN PREVIEW</text>']
    for fraction in (.2, .4, .6, .8, 1):
        parts.append(f'<polygon points="{polygon([maximum * fraction] * len(rows))}" fill="none" stroke="#694077" stroke-width="1"/>')
        parts.append(f'<text x="328" y="{cy-radius*fraction-5:.1f}" fill="#a5b5cc" font-family="Arial,sans-serif" font-size="10">{maximum*fraction:g}</text>')
    for angle, row in zip(angles, rows, strict=True):
        x, y = point(angle, radius)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#694077"/>')
        x, y = point(angle, radius + 35)
        lines = textwrap.wrap(SHORT_LABELS.get(row["measurement"], row["measurement"]), width=19)
        anchor = "start" if math.cos(angle) > .3 else "end" if math.cos(angle) < -.3 else "middle"
        spans = ''.join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else 16}">{escape(line)}</tspan>' for i, line in enumerate(lines))
        parts.append(f'<text x="{x:.1f}" y="{y-7*(len(lines)-1):.1f}" text-anchor="{anchor}" fill="#d1deed" font-family="Arial,sans-serif" font-size="13">{spans}</text>')
    parts.append(f'<polygon points="{polygon([row["reference_rate"] for row in rows])}" fill="#b69aff" fill-opacity=".14" stroke="#b69aff" stroke-width="2.5" stroke-dasharray="7 5"/>')
    if show_observed and all(row["observed_rate"] is not None for row in rows):
        parts.append(f'<polygon points="{polygon([row["observed_rate"] for row in rows])}" fill="#00ff85" fill-opacity=".22" stroke="#00ff85" stroke-width="3"/>')
        for angle, row in zip(angles, rows, strict=True):
            x, y = point(angle, radius * row["observed_rate"] / maximum)
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#00ff85"/>')
    parts.append('<text x="320" y="443" text-anchor="middle" fill="#a5b5cc" font-family="Arial,sans-serif" font-size="12">Shared rate scale · not percentiles or ability ratings</text></svg>')
    return ''.join(parts)


def reference_card(definition, profile, rows, show_observed=True):
    from pl_dna.presentation import LEGEND_CLUBS, CLUB_COLOURS
    name = definition.get("legend_inspirations", {}).get(profile, profile)
    legend = name.removesuffix("-inspired")
    club = LEGEND_CLUBS.get(name)
    accent, tint = CLUB_COLOURS.get(club, ("#b69aff", "#221c36"))
    comparison = "Move the timeline forward to compare the measured traits."
    if show_observed:
        available = [row for row in rows if row["observed_rate"] is not None]
        if available:
            closest = min(available, key=lambda row: abs(row["observed_rate"] - row["reference_rate"]))
            furthest = max(available, key=lambda row: abs(row["observed_rate"] - row["reference_rate"]))
            comparison = (f'Closest measured rate: {closest["measurement"].lower()}. '
                          f'Largest rate gap: {furthest["measurement"].lower()}.')
    return (f'<section class="dna-reference" style="border-top:4px solid {accent};background:linear-gradient(145deg,{tint},#321044);">'
            '<div class="eyebrow">LEGEND INDEX / DESIGN PREVIEW</div>'
            f'<h3>{escape(legend)} Index</h3><p>{escape(club or "Club not assigned")} · {escape(profile)}</p>'
            '<div class="dna-status">HISTORICAL BENCHMARK PENDING</div>'
            f'<p>{escape(comparison)}</p>'
            '<dl><dt>Reference season</dt><dd>Not selected yet</dd><dt>Historical source</dt><dd>Not connected yet</dd>'
            '<dt>Current reference</dt><dd>Invented demonstration rates</dd></dl>'
            '<p class="dna-note">No historical index score yet. This preview shows how the comparison will look.</p></section>')
