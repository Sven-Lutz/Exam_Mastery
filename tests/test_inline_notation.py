"""Inline markup around formulas, bare notation, topic truncation, decimal convention (RL pilot findings)."""
from exam_mastery.typeset import inline
from exam_mastery.book_model import _topic
from exam_mastery.chapter_publish import decimal_convention
from exam_mastery.labs import build as B


def test_bold_spanning_math():
    assert inline(r'**Lesarten von \(\gamma\).** Rest') == r'<strong>Lesarten von \(\gamma\).</strong> Rest'


def test_bare_notation_becomes_sub_sup():
    assert inline('V_2(High)') == 'V<sub>2</sub>(High)'
    assert inline('V^{π_neu}') == 'V<sup>π<sub>neu</sub></sup>'


def test_snake_case_and_code_untouched():
    assert inline('rl__lab.html, mdp_* und my_var') == 'rl__lab.html, mdp_* und my_var'
    assert inline('`x_1`') == '<code>x_1</code>'


def test_math_untouched():
    assert inline(r'\(V_k^{\pi}\)') == r'\(V_k^{\pi}\)'


def test_topic_never_cuts_a_formula():
    t = _topic(r'Der Agent maximiert \(J_\pi = \mathbb{E}[\sum_t \gamma^t r_t]\) über alle Policies und noch mehr Text.')
    assert t.count(r'\(') == t.count(r'\)')


def test_decimal_convention():
    assert decimal_convention({'a': 'gamma = 0.9 und 0.25, 1.000 Schritte'}) == '.'
    assert decimal_convention({'a': 'Zins 2,5 % und 0,25'}) == ','


def test_lab_fmt_follows_convention():
    try:
        B.DECIMAL['sep'] = '.'; assert B._fmt(0.7, 2) == '0.70' and B._fmt(2144.5, 1) == '2144.5'
        B.DECIMAL['sep'] = ','; assert B._fmt(2144.5, 1) == '2.144,5'
    finally:
        B.DECIMAL['sep'] = ','
