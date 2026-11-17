"""Editorial design system (B32): one set of semantic tokens shared by the typesetter (PDF/HTML), the figure kit,
the learning environment and the Anki templates. Colours are chosen for print and screen, and every semantic role
also has a non-colour cue (label text, border style or icon) so colour-vision deficiency never hides meaning.

Roles (not decoration):
  structure  navy   — headings, rules, navigation, axes
  formal     petrol — definitions, theorems, models (the 'what is true' layer)
  example    blue   — worked examples, algorithms, computed numbers
  intuition  gold   — intuition, research windows, outlook
  warning    coral  — misconceptions, counterexamples, pitfalls
  check      green  — takeaways, checks, correct answers
  practice   violet — active recall, transfer prompts, exercises
"""

TOKENS = {   # B34 palette "Atlas 2": deeper, more saturated roles; every text colour >= 4.5:1 on white and on its tint
    'navy': '#16263D', 'ink': '#1C2430', 'muted': '#556273', 'line': '#C9D1DA', 'paper': '#FFFFFF', 'wash': '#F4F6F9',
    'petrol': '#0B6E6E', 'petrol_l': '#E3F2F1', 'blue': '#24578F', 'blue_l': '#E7EFF9',
    'gold': '#8A5A00', 'gold_l': '#FDF1D8', 'coral': '#B53A2C', 'coral_l': '#FBE8E4',
    'green': '#26704A', 'green_l': '#E4F2EA', 'violet': '#3D3F96', 'violet_l': '#ECECF8',
    'plum': '#7A3B76', 'plum_l': '#F6EAF4', 'crimson': '#9E1F3F', 'crimson_l': '#FBE6EC',
}
ROLE = {'structure': 'navy', 'formal': 'petrol', 'example': 'blue', 'intuition': 'gold', 'warning': 'coral',
        'check': 'green', 'practice': 'violet'}
# typographic scale (pt in print, rem on screen); formula minimum is enforced by the layout lint
TYPE = {'body_pt': 10.6, 'small_pt': 8.6, 'h1_pt': 26, 'h2_pt': 17, 'h3_pt': 12.8, 'math_min_pt': 9.5, 'measure_em': 34,
        'line_height': 1.5}
FONT_SERIF = "'Source Serif 4',Georgia,serif"
FONT_SANS = "'Source Sans 3','Helvetica Neue',Arial,sans-serif"
FONT_MONO = "'JetBrains Mono',Menlo,monospace"


def css_vars():
    return ':root{' + ''.join(f'--{k.replace("_", "-")}:{v};' for k, v in TOKENS.items()) + '}'


def diverging(v, lo, hi):
    """Value colour for heatmaps: coral (negative) -> white (0) -> petrol (positive); symmetric, print-safe.
    Numbers are always printed in the cell as well (colour is never the only carrier)."""
    def mix(a, b, t):
        a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
        return '#' + ''.join(f'{round(x + (y - x) * t):02x}' for x, y in zip(a, b))
    if v is None:
        return TOKENS['wash']
    if v >= 0:
        return mix('#FFFFFF', '#5FA9A6', min(1.0, v / (hi or 1)) * 0.9)
    return mix('#FFFFFF', '#E58A7C', min(1.0, v / (lo or -1)) * 0.9)
