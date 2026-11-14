from __future__ import annotations
import ast, csv, html, json, math, os, re
from pathlib import Path
from .common import write_json
from .validate import numeric_ast, evaluate_numeric

ESC=lambda x:html.escape(str(x),quote=True)
MARKING_LABELS={'method_credit':'Method credit','follow_through':'Carried arithmetic errors','alternatives':'Equivalent solutions'}

def reading_labels(mode):
    return {'case_law':('Issue and facts','Rule and application','Reasoned conclusion'),'experimental':('Observation and question','Method and uncertainty','Analysis and interpretation'),'computational':('Problem and invariant','Algorithm and reasoning','Execution trace')}.get(mode,('Intuition','Formal reasoning','Worked example'))

def rich_text(value):
    """Escape first; support conservative plain-text mathematical indices/powers.

    Only single-letter mathematical bases are indexed; prose identifiers and
    arbitrary source HTML remain inert. Complex TeX is not silently interpreted.
    """
    text=ESC(value)
    subs=str.maketrans('₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎','0123456789+−=()')
    sups=str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾','0123456789+−=()')
    text=re.sub('[₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎]+',lambda m:'<sub>'+m[0].translate(subs)+'</sub>',text)
    text=re.sub('[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾]+',lambda m:'<super>'+m[0].translate(sups)+'</super>',text)
    text=re.sub(r'\*\*([^*\n]+)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'\b([a-z]?[A-Z]|[A-Za-z])_(\([^()\n]+\)|[A-Za-z]|[0-9]+)',lambda m:m[1]+'<sub>'+m[2].removeprefix('(').removesuffix(')')+'</sub>',text)
    text=re.sub(r'\^(\([^()\n]+\)|[A-Za-z]|[0-9]+(?:\.[0-9]+)?)',lambda m:'<super>'+m[1].removeprefix('(').removesuffix(')')+'</super>',text)
    return text

def _p(x): return '<p>'+rich_text(x).replace('<super>','<sup>').replace('</super>','</sup>').replace('\n','<br>')+'</p>' 

def _ast_json(node):
    if isinstance(node,ast.Expression): return _ast_json(node.body)
    if isinstance(node,ast.Constant): return {'n':node.value}
    if isinstance(node,ast.Name): return {'v':node.id}
    if isinstance(node,ast.UnaryOp): return {'u': '+' if isinstance(node.op,ast.UAdd) else '-', 'arg':_ast_json(node.operand)}
    ops={ast.Add:'+',ast.Sub:'-',ast.Mult:'*',ast.Div:'/',ast.Pow:'**'}
    return {'op':ops[type(node.op)],'a':_ast_json(node.left),'b':_ast_json(node.right)}

def publish_html(bp,author,assess,cards,interaction,design,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    lab_nav='<a href="#lab">Lab</a>' if interaction['kind']!='none' else ''
    title=ESC(bp['title']); css=(Path(__file__).parent/'templates'/'main.css').read_text(encoding='utf-8')
    d=design['theme'];font='Georgia,serif' if design['layout']['heading_family']=='serif' else 'system-ui,sans-serif'
    theme=f':root{{--ink:{d["ink"]};--blue:{d["accent"]};--paper:{d["paper"]};--surface:{d["surface"]}}}'
    css=css.replace('}','}'+theme,1)+f'h1,h2{{font-family:{font}}}' 
    from .math_publishing import prepare,markup
    registry=prepare(author.get('mathematics',[]),out.parent/'math')
    if registry:write_json(out.parent/'math/registry.json',registry)
    def ptext(value):return '<p>'+markup(value,registry,'web',rich_text).replace('<super>','<sup>').replace('</super>','</sup>').replace('\n','<br>')+'</p>'
    mode=design.get('presentation_mode','general')
    labels={'case_law':('Issue and facts','Rule and application','Reasoned conclusion'),'experimental':('Observation and question','Method and uncertainty','Analysis and interpretation'),'computational':('Problem and invariant','Algorithm and reasoning','Execution trace')}.get(mode,('Intuition','Formal reasoning','Worked example'))
    css+=' .em-figure-scroll{max-width:100%;overflow-x:auto}.em-math-scroll{display:block;max-width:100%;overflow-x:auto}.em-math{display:inline-block;max-width:100%;overflow-x:auto;vertical-align:middle}.em-math > svg{max-width:none;height:auto;display:block} .equations{border-top:2px solid var(--blue)}'
    blocks=[]
    blocks.append(f'<section id="intro" class="lede"><span class="eyebrow">EXAM MASTERY · STUDY EDITION</span><h1>{title}</h1><p>{ESC(bp.get("domain_summary",""))}</p><div class="chips">'+''.join(f'<span>{ESC(c["operation"])}</span>' for c in bp['competencies'])+'</div></section>')
    blocks.append('<section id="goals"><h2>Learning objectives</h2><ol>'+''.join(f'<li><strong>{ESC(c["id"])}</strong> — {ESC(c["statement"])}</li>' for c in bp['competencies'])+'</ol></section>')
    for c in author.get('prerequisite_checks',[]):
        blocks.append('<section class="task"><h2>Entry check: '+ESC(c['prerequisite'])+'</h2>'+ptext(c['prompt'])+'<details><summary>Check and repair</summary>'+ptext(c['solution'])+ptext(c['pass_criterion'])+ptext(c['error_diagnosis'])+ptext(c['remediation'])+ptext(c['retry_prompt'])+'<details><summary>Retry solution</summary>'+ptext(c['retry_solution'])+'</details></details></section>')
    for i,s in enumerate(author['sections'],1):
        labels=reading_labels(s.get('presentation_mode',mode))
        blocks.append(f'<section id="section-{i}"><div class="eyebrow">CHAPTER {i:02d}</div><h2>{ESC(s["title"])}</h2><h3>{labels[0]}</h3>{ptext(s["intuition"])}<h3>{labels[1]}</h3>{ptext(s["formal"])}<div class="worked"><span class="eyebrow">{labels[2]}</span>{ptext(s["worked_example"])}</div>')
        # Visual specifications remain in the model; publish actual rendered figures below.
        if s.get('misconceptions'): blocks.append('<h3>Typical misconceptions</h3><ul>'+''.join(f'<li>{ESC(m)}</li>' for m in s['misconceptions'])+'</ul>')
        blocks.append('<p class="sources">Source anchors: '+', '.join(map(ESC,s['source_refs']))+'</p></section>')
    if registry:
        blocks.append('<section class="equations" id="equations"><h2>Mathematical reference</h2>')
        for equation in registry.values():
            r=equation['record'];ident=r['id']
            blocks.append('<article id="eq-'+ESC(ident)+'"><h3>Equation ('+str(equation['number'])+')</h3>'+ptext('[[math:'+ident+']]')+ptext(r['alt'])+ptext('Domain: '+r['domain'])+ptext('Assumptions: '+'; '.join(r['assumptions']))+ptext('Source anchors: '+', '.join(r['source_refs']))+'<dl>'+''.join('<dt>'+ESC(v['name'])+'</dt><dd>'+ESC(v['definition']+'; '+v['domain']+'; unit '+v['unit'])+'</dd>' for v in r['symbols'])+'</dl></article>')
        blocks.append('</section>')
    if interaction['kind'] != 'none':
        canonical_lab=''
        if interaction.get('math_id') in registry:
            canonical_lab='<template id="lab-formula-template">'+markup('[[math:'+interaction['math_id']+']]',registry,'web',rich_text)+'</template>'
        blocks.append('<section id="lab"><span class="eyebrow">EXPERIMENT</span><h2>'+ESC(interaction.get('title','Interactive learning'))+'</h2><p>'+ESC(interaction['reason'])+'</p>'+canonical_lab+'<div id="lab-root" class="lab" aria-live="polite"></div></section>')
    blocks.append('<section id="practice"><span class="eyebrow">ASSESSMENT</span><h2>Independent practice</h2><p>Attempt each problem before opening its model solution.</p>')
    for a in assess['items']:
        policy=a.get('marking_policy',{})
        support=''.join(ptext(MARKING_LABELS.get(k,k)+': '+v) for k,v in policy.items())+''.join(ptext(d['error']+' — '+d['diagnosis']+' → '+d['remediation']) for d in a.get('error_diagnoses',[]))
        rub='<ul>'+''.join(f'<li>{ESC(x["criterion"])} ({x["points"]} pt) — {ESC(x.get("partial_credit",""))}</li>' for x in a['rubric'])+'</ul>'
        attached=''.join('<div data-solution-figure="'+ESC(ident)+'"></div>' for ident in a.get('figure_ids',[]))
        blocks.append(f'<article class="task"><h3>{ESC(a["id"])} · {ESC(a["difficulty"])} · {a["points"]} points</h3>{ptext(a["prompt"])}<details><summary>Reveal solution and grading rubric</summary>{ptext(a["solution"])}{attached}<h4>Rubric</h4>{rub}{support}</details></article>')
    blocks.append('</section>')
    if author.get('limitations'): blocks.append('<section><h2>Scope and limitations</h2><ul>'+''.join('<li>'+ESC(x)+'</li>' for x in author['limitations'])+'</ul></section>')
    blocks.append('<footer>Draft learning package · Source-grounded references are locator identifiers, not externally verified URLs. No claimed empirical learning validation.</footer>')
    js_data=json.dumps(interaction,ensure_ascii=False).replace('<','\\u003c')
    if interaction['kind']=='numeric':
        numeric=interaction['numeric']; tree=_ast_json(numeric_ast(numeric['expression'],{numeric['variable'],*numeric['constants'].keys()}))
        js_data=json.dumps({**interaction,'compiled_expression':tree},ensure_ascii=False).replace('<','\\u003c')
    script=(Path(__file__).parent/'templates'/'lab.js').read_text(encoding='utf-8')
    doc=f'''<!doctype html><html lang="{ESC(bp.get("language","en"))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Exam Mastery</title><style>{css}</style></head><body><a class="skip" href="#main">Zum Inhalt</a><div class="shell"><aside class="sidebar"><strong>EXAM <span>MASTERY</span></strong><nav aria-label="Sections"><a href="#intro">Overview</a><a href="#goals">Objectives</a>{''.join(f'<a href="#section-{i}">Chapter {i}</a>' for i,_ in enumerate(author['sections'],1))}{lab_nav}<a href="#practice">Practice</a></nav></aside><main id="main">{''.join(blocks)}</main></div><script id="lab-spec" type="application/json">{js_data}</script><script>{script}</script></body></html>'''
    (out/'index.html').write_text(doc,encoding='utf-8')
    return out/'index.html'

def publish_cards(bp,cards,design,out:Path,mathematics=(),figure_records=()):
    out.mkdir(exist_ok=True,parents=True)
    from .math_publishing import prepare,markup
    import shutil
    registry=prepare(list(mathematics),out/'media')
    for record in figure_records:
        source=Path(record.get('png',record['path']));(out/'media').mkdir(exist_ok=True);shutil.copy2(source,out/'media'/source.name)
    css=(Path(__file__).parent/'templates'/'anki.css').read_text(encoding='utf-8')
    d=design['theme'];css=css+f'.card{{color:{d["ink"]};background:{d["surface"]}}}.em-card{{background:{d["paper"]}}}.em-kicker{{color:{d["accent"]}}}.nightMode .em-kicker{{color:#9dcced}}' 
    css+=' .em-figure-scroll{max-width:100%;overflow-x:auto}.em-math-scroll{display:block;max-width:100%;overflow-x:auto}.em-math{max-width:100%;object-fit:contain;vertical-align:middle}.nightMode img.em-math{filter:invert(1)}'
    (out/'anki_style.css').write_text(css,encoding='utf-8')
    (out/'anki_front.html').write_text('<div class="em-card"><div class="em-kicker">ACTIVE RECALL</div><div class="em-question">{{Question}}</div></div>',encoding='utf-8')
    (out/'anki_back.html').write_text('<div class="em-card"><div class="em-kicker">ANSWER</div><div class="em-question">{{Question}}</div><hr id="answer"><div class="em-answer">{{Answer}}</div><div class="em-explanation">{{Explanation}}</div><div class="em-source">{{Source}}</div></div>',encoding='utf-8')
    with (out/'anki_import.tsv').open('w',encoding='utf-8',newline='') as f:
        f.write('#separator:Tab\n#html:true\n#columns:ID\tQuestion\tAnswer\tExplanation\tSource\n')
        writer=csv.writer(f,delimiter='\t',lineterminator='\n')
        for c in cards['cards']:
            def flat(s): return markup(s,registry,'anki',rich_text).replace('<super>','<sup>').replace('</super>','</sup>').replace('\n','<br>')
            figure_html=''
            by_id={r.get('id'):r for r in figure_records if r.get('id')}
            for ident in c.get('figure_ids',[]):
                if ident not in by_id:
                    if not figure_records:continue
                    raise ValueError('Card references unrendered figure '+ident)
                record=by_id[ident];figure_html+='<figure style="margin:0"><div class="em-figure-scroll" tabindex="0"><img src="'+Path(record.get('png',record['path'])).name+'" alt="'+ESC(record['alt_text'])+'" style="min-width:650px;width:100%;max-width:none"></div><figcaption>'+ESC(record.get('caption',record['alt_text']))+'</figcaption></figure>'
            writer.writerow([bp.get('course_id','course')+':'+c['id'],flat(c['question']),flat(c['answer'])+figure_html,flat(c['explanation']),', '.join(c['source_refs'])])
    (out/'IMPORT.md').write_text(f'''# Anki import contract

Deck: {bp['title']}

1. Create a custom Anki note type with fields: `ID`, `Question`, `Answer`, `Explanation`, `Source` **in that order**.
2. Set its Front/Back templates to `anki_front.html` and `anki_back.html`, and its Styling to `anki_style.css`.
3. Import `anki_import.tsv`, selecting this note type and enabling HTML in fields. Keep `ID` as the **first field**.
4. Enable duplicate/update by **note type** on future imports so identical IDs replace fields while keeping scheduling.
5. Verify formatting in actual Anki Desktop and mobile client; browser preview is NOT a substitute.

Do not use arbitrary GUID values. Anki's own GUID management remains authoritative. These cards contain no JavaScript.\n''',encoding='utf-8')

def register_fonts():
    """Register a locally installed Unicode font pair for reportlab; Helvetica as last resort."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    # Locally installed fonts only; never distribute font files in the engine.
    import matplotlib
    local_fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
    candidates=[
        (os.getenv('EXAM_MASTERY_FONT',''),os.getenv('EXAM_MASTERY_FONT_BOLD','')),
        (str(local_fonts/'DejaVuSans.ttf'),str(local_fonts/'DejaVuSans-Bold.ttf')),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('/System/Library/Fonts/Supplemental/Arial.ttf','/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
        ('/Library/Fonts/Arial.ttf','/Library/Fonts/Arial Bold.ttf'),
    ]
    font='Helvetica';fontbold='Helvetica-Bold'
    for normal,bold in candidates:
        if normal and bold and Path(normal).is_file() and Path(bold).is_file():
            try:
                if 'EMSystem' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('EMSystem',normal))
                if 'EMSystemBold' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('EMSystemBold',bold))
                font='EMSystem';fontbold='EMSystemBold';break
            except Exception: continue
    return font,fontbold

def publish_pdf(bp,author,assess,interaction,design,out:Path,figure_records=()):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, PageBreak, HRFlowable, Image, LongTable, TableStyle
    from reportlab.graphics.shapes import Drawing, PolyLine, Circle, String, Line
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    font,fontbold=register_fonts()
    navy=colors.HexColor(design['theme']['ink']); blue=colors.HexColor(design['theme']['accent'])
    style={
      'title':ParagraphStyle('title',fontName=fontbold,fontSize=23,leading=30,textColor=navy,spaceAfter=16),
      'h1':ParagraphStyle('h1',fontName=fontbold,fontSize=15,leading=22,textColor=navy,spaceBefore=18,spaceAfter=9,keepWithNext=True),
      'h2':ParagraphStyle('h2',fontName=fontbold,fontSize=10,leading=16,textColor=blue,spaceBefore=11,spaceAfter=5,keepWithNext=True),
      'body':ParagraphStyle('body',fontName=font,fontSize=10.2,leading=16,spaceAfter=9,allowOrphans=0,allowWidows=0),
      'small':ParagraphStyle('small',fontName=font,fontSize=8.5,leading=12,textColor=colors.HexColor('#405267'),spaceAfter=8),
    }
    def par(text,st='body'):
        return Paragraph(rich_text(text).replace('\n','<br/>'),style[st])
    section_labels={'case_law':('Issue and facts','Rule and application','Reasoned conclusion'),'experimental':('Observation and question','Method and uncertainty','Analysis and interpretation'),'computational':('Problem and invariant','Algorithm and reasoning','Execution trace')}.get(design.get('presentation_mode'),('Intuition','Formal reasoning','Worked example'))
    from .math_publishing import prepare,markup,formula_plates
    registry=prepare(author.get('mathematics',[]),out.parent/'math')
    original_par=par
    def par(text,st='body'):
        # Display equations are genuine vector flowables with their own measured height.
        from .math_publishing import TOKEN
        from svglib.svglib import svg2rlg
        pieces=[];last=0
        for match in TOKEN.finditer(str(text)):
            if match[1]!='math':continue
            ident=match[2]
            if ident not in registry:raise ValueError('Undefined mathematical reference '+ident)
            prefix=str(text)[last:match.start()]
            if prefix.strip():pieces.append(Paragraph(markup(prefix,registry,'pdf',rich_text).replace('\n','<br/>'),style[st]))
            equation=registry[ident]
            diagram=svg2rlg(equation['svg']);factor=min(1,470/diagram.width)
            diagram.scale(factor,factor);diagram.width*=factor;diagram.height*=factor
            pieces.extend([Spacer(1,8),diagram,Paragraph('Equation ('+str(equation['number'])+') · '+ESC(', '.join(equation['record']['source_refs'])),style['small']),Spacer(1,8)])
            last=match.end()
        if not pieces:return Paragraph(markup(text,registry,'pdf',rich_text).replace('\n','<br/>'),style[st])
        suffix=str(text)[last:]
        if suffix.strip():pieces.append(Paragraph(markup(suffix,registry,'pdf',rich_text).replace('\n','<br/>'),style[st]))
        return KeepTogether(pieces)

    flow=[par('EXAM MASTERY  ·  LEHRBUCHENTWURF','small'),par(bp['title'],'title'),par(bp.get('domain_summary','')),Spacer(1,12),HRFlowable(width='100%',thickness=1,color=blue),par('Kompetenzziele','h1')]
    for i,c in enumerate(bp['competencies'],1): flow.append(par(str(i)+'. '+c['statement']))
    for c in author.get('prerequisite_checks',[]):
        flow.extend([par('Entry check: '+c['prerequisite'],'h1'),par(c['prompt']),par('Self-check and repair','h2'),par(c['solution']),par(c['pass_criterion']),par(c['error_diagnosis']),par(c['remediation']),par('Retry: '+c['retry_prompt']),par('Retry solution: '+c['retry_solution'])])
    for i,s in enumerate(author['sections'],1):
        section_labels=reading_labels(s.get('presentation_mode',design.get('presentation_mode')))
        flow.extend([par(re.sub(r'^\d+[.)]\s*','',s["title"]),'h1'),par(section_labels[0],'h2'),par(s['intuition']),par(section_labels[1],'h2'),par(s['formal']),par(section_labels[2],'h2'),par(s['worked_example'])])
        if s.get('misconceptions'):
            flow.append(par('Typische Denkfehler','h2'))
            for x in s['misconceptions']:flow.append(par('• '+x))
        # Do not publish prose specifications as a substitute for actual figures.
        flow.append(par('Quellenanker: '+', '.join(s['source_refs']),'small'))
    if registry:
        flow.append(par('Mathematical reference','h1'));flow.extend(formula_plates(registry))
    def figure_block(record):
        from PIL import Image as PILImage
        if Path(record['path']).suffix=='.svg':
            from svglib.svglib import svg2rlg
            diagram=svg2rlg(record['path']);scale=min(490/diagram.width,460/diagram.height);diagram.scale(scale,scale);diagram.width*=scale;diagram.height*=scale;graphic=diagram
        else:
            with PILImage.open(record['path']) as im: width,height=im.size
            scale=min(490/width,460/height);graphic=Image(record['path'],width=width*scale,height=height*scale)
        return KeepTogether([par(record['title'],'h2'),graphic,par(record.get('caption',record['alt_text'])),par('Source anchors: '+', '.join(record['source_refs']),'small')])
    for record in figure_records:flow.append(figure_block(record))
    if interaction['kind']=='numeric' and not interaction.get('math_id'):
        n=interaction['numeric'];x0,x1=n['min'],n['max']
        samples=[x0+(x1-x0)*i/60 for i in range(61)]
        ys=[evaluate_numeric(n['expression'],{**n['constants'],n['variable']:x}) for x in samples]
        ylo,yhi=min(ys),max(ys);dy=max(yhi-ylo,1e-9)
        graph=Drawing(470,220)
        graph.add(Line(40,30,440,30,strokeColor=colors.HexColor('#829cae')))
        graph.add(Line(40,30,40,186,strokeColor=colors.HexColor('#829cae')))
        coords=[]
        for x,y in zip(samples,ys):coords.extend([40+(x-x0)/(x1-x0)*400,30+(y-ylo)/dy*156])
        graph.add(PolyLine(coords,strokeColor=blue,strokeWidth=2.4))
        y0=evaluate_numeric(n['expression'],{**n['constants'],n['variable']:n['default']})
        graph.add(Circle(40+(n['default']-x0)/(x1-x0)*400,30+(y0-ylo)/dy*156,5,fillColor=colors.HexColor('#bc8637'),strokeColor=None))
        graph.add(String(40,5,str(x0),fontName=font,fontSize=8))
        graph.add(String(425,5,str(x1),fontName=font,fontSize=8))
        graph.add(String(45,196,n.get('value_label','Response'),fontName=font,fontSize=9))
        flow.extend([par('Interaktives Modell als statische Lernabbildung','h1'),par('Sensitivitaet der Zielgroesse auf die Variable '+n.get('label',n['variable'])+'; alle uebrigen Modellgroessen konstant.'),graph])
    flow.extend([PageBreak(),par('Übungs- und Aufgabenbuch','title'),par('Aufgaben zunächst ohne die Musterlösungen bearbeiten.')])
    for a in assess['items']:
        flow.extend([par(f'{a["id"].rsplit(":",1)[-1]}: {a["difficulty"]} ({a["points"]} P.)','h1'),par(a['prompt']),Spacer(1,27)])
    flow.extend([PageBreak(),par('Musterlösungen und Rubrics','title')])
    for a in assess['items']:
        flow.extend([par(a['id'].rsplit(':',1)[-1],'h1'),par(a['solution'])])
        by_figure={f['id']:f for f in figure_records if f.get('id')}
        for ident in a.get('figure_ids',[]):
            if ident in by_figure:flow.append(figure_block(by_figure[ident]))
        rows=[[par('Rubric — '+a['id'].rsplit(':',1)[-1],'h2'),par('Points','h2')]]
        rows += [[par(r['criterion']+' '+r.get('partial_credit','')),par(str(r['points']))] for r in a['rubric']]
        table=LongTable(rows,colWidths=[440,63],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),0.7,blue),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f5f8')])]))
        flow.append(table)
        for k,v in a.get('marking_policy',{}).items():flow.append(par(MARKING_LABELS.get(k,k)+': '+v))
        for d in a.get('error_diagnoses',[]):flow.append(par(d['error']+' — '+d['diagnosis']+' → '+d['remediation']))
    if author['limitations']:
        flow.append(KeepTogether([par('Grenzen und offene Fragen','h1')]+[par('• '+x) for x in author['limitations']]))
    out.parent.mkdir(exist_ok=True,parents=True)
    pdf=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=57,bottomMargin=52,
          title=bp['title']+' | Exam Mastery DRAFT',author='Exam Mastery Studio')
    def footer(c,doc):
        c.setFont(font,7.5);c.setFillColor(colors.HexColor('#64748b'))
        c.drawString(46,31,'EXAM MASTERY · DRAFT — nicht fachlich freigegeben')
        c.drawRightString(A4[0]-46,31,str(doc.page))
    pdf.build(flow,onFirstPage=footer,onLaterPages=footer)
    return out

def publish_all(bp,author,assess,cards,interaction,design,run_dir):
    out=run_dir/'artifacts'
    publish_html(bp,author,assess,cards,interaction,design,out/'web')
    publish_cards(bp,cards,design,out/'anki',author.get('mathematics',[]))
    publish_pdf(bp,author,assess,interaction,design,out/'learning_package.pdf')
    return out
