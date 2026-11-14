"""Generic slide-deck course (SYNTHETIC_FIXTURE): a paged lecture PDF whose page titles become topic competencies,
plus a question catalogue. Pages cover the shapes that must be told apart: an arithmetic calculation, a totals
table, a quantity question, a chart without numbers in the text, a page that only states figures, and a list."""
import tempfile
from pathlib import Path

PAGES = [
    ('Valuation Basics', ['A firm raises capital from investors.', 'Ownership is expressed in shares.']),
    ('Example: Second Round', ['Pre-money value 4 Mio EUR, new investment 1 Mio EUR.',
                               'POM = 4 Mio EUR + 1 Mio EUR = 5,000,000 EUR', 'Share of the investor = 1/5 = 20 %']),
    ('Cap Table after Round 1', ['Founders 40,000', 'Investor A 10,000', 'Investor B 50,000', 'Sum 100,000']),
    ('How much must the investor pay?', ['Use the post-money value from the previous page.']),
    ('Market Volume', ['(Source: Market Monitor, p. 12)']),
    ('Fund Facts', ['The fund manages about 900 million EUR in three funds.', 'Typical ticket 600,000 EUR.']),
    ('Top Reasons for Failure', ['Run out of capital', 'No market need', 'Team problems']),
]
QUESTIONS = '''Session 1

1. Name the three top reasons for failure.
2. What is the definition of a share according to the lecture?
'''


def make(base=None):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape, A4
    root = Path(base or tempfile.mkdtemp(prefix='emslides-')) / 'Kurs Finanzierung'
    root.mkdir(parents=True)
    c = canvas.Canvas(str(root / '01 Finance Lecture.pdf'), pagesize=landscape(A4))
    for n, (title, lines) in enumerate(PAGES, 1):
        c.setFont('Helvetica-Bold', 28); c.drawString(50, 520, title)
        c.setFont('Helvetica', 16)
        for i, ln in enumerate(lines):
            c.drawString(60, 460 - 32 * i, ln)
        c.setFont('Helvetica', 9); c.drawString(780, 20, str(n)); c.showPage()
    c.save()
    (root / 'Fragenkatalog.md').write_text(QUESTIONS, encoding='utf-8')
    return root
