"""Unabhängige Prüfung der eigenen NLP-Beispiele für den Modulvertrag (Python-Orakel, nicht der JS-Kern)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
import v5_attention as V5  # noqa: E402
from exam_mastery.reference_unit import attn_full  # noqa: E402


def bank():
    r = attn_full(V5.BANK)
    assert [round(x, 4) for x in r['w']] == [0.5904, 0.1037, 0.3059]
    assert [round(x, 4) for x in r['o']] == [1.1343, 0.3763]
    shifted = dict(V5.BANK, K=[[k[0] + 3.7, k[1] - 2.2] for k in V5.BANK['K']])
    assert all(abs(a - b) < 1e-12 for a, b in zip(attn_full(shifted)['w'], r['w'])), 'Satz 6.1a'
    return {'w': [round(x, 4) for x in r['w']], 'o': [round(x, 4) for x in r['o']]}


def jacobian_ties():
    def J(s, T):
        e = [math.exp((x - max(s)) / T) for x in s]; w = [x / sum(e) for x in e]
        return math.sqrt(sum(((w[i] if i == j else 0) - w[i] * w[j]) ** 2 for i in range(len(w)) for j in range(len(w)))) / T
    assert J([1, 0, -.5], .01) < 1e-6 and J([1, 1, -.5], .01) > 30, 'Lemma 6.4 (b) und (c)'
    return {'unique_T0.01': J([1, 0, -.5], .01), 'tie_T0.01': J([1, 1, -.5], .01)}
