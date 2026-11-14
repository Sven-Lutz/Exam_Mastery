"""P3.3 synthetic fixtures: slide-style PDFs with real layout properties (title font, footers, template vectors,
scans, charts), templates, administration briefings, question catalogues and a business course. No real course data."""
import io
from pathlib import Path


def _png(size=(400, 300), color='gray'):
    from PIL import Image
    b = io.BytesIO(); Image.new('RGB', size, color).save(b, 'PNG'); return b.getvalue()


def slide_pdf(path, pages, footer='Course Footer Line', template_lines=3):
    """pages: list of dicts {title, body:[lines], image:(w,h)|None, chart_paths:int, scan:bool}"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    W, H = 960, 540
    cv = canvas.Canvas(str(path), pagesize=(W, H))
    for p in pages:
        if p.get('scan'):
            cv.drawImage(ImageReader(io.BytesIO(_png((800, 450)))), 80, 40, 800, 450)
            for i in range(template_lines):
                cv.line(20, 20 + i, 940, 20 + i)
            cv.showPage(); continue
        for i in range(template_lines):  # page-template decoration: same few vector lines on every page
            cv.line(20, 500 - i * 2, 940, 500 - i * 2)
        if p.get('title'):
            cv.setFont('Helvetica-Bold', 26); cv.drawString(40, 470, p['title'])
        cv.setFont('Helvetica', 14); y = 420
        for ln in p.get('body', []):
            # body lines get a page-specific suffix so that only real running lines (footer) repeat across pages
            cv.drawString(60, y, ln if p.get('raw') or ln.startswith(('-', 'What')) or len(p.get('body', [])) < 3 else f"{ln} (slide {pages.index(p) + 1})"); y -= 22
        cv.setFont('Helvetica', 9); cv.drawString(40, 15, footer)
        if p.get('image'):
            w, h = p['image']; cv.drawImage(ImageReader(io.BytesIO(_png((w, h), 'blue'))), 560, 80, w, h)
        for i in range(p.get('chart_paths', 0)):  # a real vector chart: many bars
            cv.rect(560 + i * 6, 80, 4, 20 + (i * 7) % 120, fill=1)
        cv.showPage()
    cv.save()
    return path


BODY = ['Opportunities arise from changes in markets and technology.', 'Founders combine resources to exploit them.',
        'The process is iterative and evidence driven.', 'Customers validate value propositions in interviews.',
        'Pricing reflects willingness to pay and costs.', 'Teams learn from experiments and pivots.']


def lecture_deck(root, name='lecture_markets.pdf', n=12, scan_page=None, extra=None):
    pages = []
    words = ['Pricing', 'Segmentation', 'Positioning', 'Channels', 'Retention', 'Partnerships', 'Licensing', 'Bootstrapping',
             'Hiring', 'Scaling', 'Exit', 'Governance', 'Forecasting', 'Benchmarking', 'Procurement', 'Branding']
    for i in range(1, n + 1):
        pages.append({'title': f'{words[i - 1]} decisions', 'body': BODY})
    pages[0] = {'title': 'Market Dynamics and Opportunities', 'body': ['Lecture overview of market dynamics and entry decisions'] + BODY[:2]}
    if scan_page:
        pages[scan_page - 1] = {'scan': True}
    for k, v in (extra or {}).items():
        pages[k - 1] = v
    return slide_pdf(Path(root) / name, pages)


def inflation_deck(root):
    """Footer on every page, citation lines, numeric chart labels, repeated titles, figure legends."""
    pages = [{'title': 'Funding Sources', 'body': ['Inspired by Smith et al. 2011, Pos. 497', '2', '14', '(€, thousand)', 'Equity and debt differ in risk.']}]
    for i in range(2, 9):
        title = 'Funding Sources' if i <= 4 else f'Valuation step {i}'
        pages.append({'title': title, 'body': ['Smith, J. (2015). Finance basics. p. 12', '3', '…', 'Investors price risk in rounds.']})
    pages.append({'title': 'References', 'body': ['Smith, J. (2015). Finance basics.', 'Doe, A. (2019). Startups.']})
    return slide_pdf(Path(root) / 'funding.pdf', pages, footer='Repeated Footer – Course Title')


def admin_briefing(root):
    pages = [{'title': 'Lecture Information', 'body': ['Prof. Dr. Example', 'contact: lecturer@uni.example']},
             {'title': 'Exam', 'body': ['Exam date: Monday 12:00, Room 101', 'Grade in exam: bonus for case study', 'Registration via ILIAS']},
             {'title': 'Dates', 'body': ['Attendance compulsory', 'Deadline for submission: Friday 23:55', 'Office hours on request']},
             {'title': 'Credits', 'body': ['6 ECTS credit points', 'Exam registration until deadline', 'Contact the office by e-mail office@uni.example']}]
    return slide_pdf(Path(root) / 'organisation_slides.pdf', pages)


def templates(root):
    from pptx import Presentation
    from docx import Document
    prs = Presentation(); s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = 'Sample headline: Arial 24pt bold'; s.placeholders[1].text = 'Lorem ipsum dolor sit amet, consetetur sadipscing'
    prs.save(Path(root) / 'Template_Presentation.pptx')
    d = Document(); d.add_heading('Chapter heading', 1); d.add_paragraph('Insert your text here. Font: Arial 11pt.')
    d.add_heading('Introduction', 1); d.add_paragraph('Lorem ipsum dolor sit amet.')
    d.save(Path(root) / 'Vorlage_Hausarbeit.docx')


def question_catalogue(root):
    lines = ['Question Catalogue', '1. What is a value proposition according to the lecture?', '2. Name the three pricing strategies.',
             '3. Explain the difference between equity and debt financing.', '4. Calculate the break-even quantity for fixed costs of 1000 and a margin of 20.',
             '5. Compare bootstrapping and venture capital.', '6. Define market potential.']
    return slide_pdf(Path(root) / 'question_catalogue.pdf', [{'title': 'Question Catalogue', 'body': lines[1:]}])


BUSINESS_MD = '''# Unit Economics and Break-even

## Lernziele
- Berechnen Sie den Break-even-Punkt eines Start-ups aus Fixkosten und Deckungsbeitrag.
- Erklären Sie den Zusammenhang zwischen Preis, Kosten und Gewinn.

Der Deckungsbeitrag je Einheit ist Preis minus variable Kosten. Der Break-even-Punkt ist die Menge, bei der der Gewinn null ist: Fixkosten geteilt durch Deckungsbeitrag je Einheit. Investoren, Kunden und Markt bestimmen Preisspielräume; Finanzierung und Umsatz hängen davon ab.
'''
BUSINESS_PRACTICE = '''# Übungsfragen

1. Berechnen Sie den Break-even-Punkt bei Fixkosten von 12000 Euro, Preis 50 Euro und variablen Kosten 30 Euro.
2. Erklären Sie, wie eine Preiserhöhung Kosten, Umsatz und Gewinn beeinflusst.
'''


def business_course(root):
    root = Path(root)
    (root / 'vorlesung_unit_economics.md').write_text(BUSINESS_MD, encoding='utf-8')
    (root / 'uebungsfragen.md').write_text(BUSINESS_PRACTICE, encoding='utf-8')
    (root / 'exam.md').write_text('# Klausur\n\nAufgabe 1\nGegeben sind Fixkosten von 8000 Euro und ein Deckungsbeitrag von 40 Euro. '
                                  'Berechnen Sie den Break-even-Punkt. (4 P)\n', encoding='utf-8')
    return root
