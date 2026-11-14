"""P3.3: evidence-based source-role triage, page model, competency-candidate filter and visual relevance classes.

Deterministic and offline. Every decision carries the signal that produced it and the original element/locator, so a
reviewer can overrule it. Nothing here deletes inventory content; rejected candidates are kept with their reason.
The vocabularies below are generic course/document vocabulary (administration, templates, question formats), not
subject or course content. Unclear cases are REVIEW_REQUIRED, never silently classified.
"""
import re
from collections import Counter

ROLES = ('ACADEMIC_CONTENT', 'COURSE_ADMINISTRATION', 'TEMPLATE_LAYOUT', 'CASE_STUDY_BRIEF', 'PRACTICE_QUESTIONS',
         'ASSESSMENT_EXAM', 'ASSESSMENT_SOLUTION', 'SUPPORTING_MATERIAL', 'REVIEW_REQUIRED',
         'CASE_STUDY_WORK', 'REFERENCE_LITERATURE', 'DUPLICATE', 'SUPERSEDED_VERSION', 'SYSTEM_IGNORED')
# B6.3: one stable category per source on top of the role. Extensible: add a role and map it here.
CATEGORY_OF_ROLE = {'ACADEMIC_CONTENT': 'OFFICIAL_LECTURE', 'PRACTICE_QUESTIONS': 'EXERCISE_QUESTIONS',
                    'ASSESSMENT_EXAM': 'EXERCISE_QUESTIONS', 'ASSESSMENT_SOLUTION': 'EXERCISE_QUESTIONS',
                    'CASE_STUDY_BRIEF': 'CASE_STUDY_ASSIGNMENT', 'CASE_STUDY_WORK': 'CASE_STUDY_ASSIGNMENT',
                    'SUPPORTING_MATERIAL': 'SUPPLEMENTARY', 'REFERENCE_LITERATURE': 'REFERENCE_LITERATURE',
                    'COURSE_ADMINISTRATION': 'COURSE_ADMINISTRATION', 'TEMPLATE_LAYOUT': 'TEMPLATE',
                    'REVIEW_REQUIRED': 'OTHER_UNRESOLVED', 'DUPLICATE': 'DUPLICATE', 'SUPERSEDED_VERSION': 'SUPERSEDED_VERSION',
                    'SYSTEM_IGNORED': 'SYSTEM_IGNORED'}
CATEGORIES = {'OFFICIAL_LECTURE': 'lecture / session material; the only category that forms subject chapters',
              'EXERCISE_QUESTIONS': 'question catalogues, exercises, exams, solutions; linked to chapters, never chapters',
              'CASE_STUDY_ASSIGNMENT': 'case-study briefs and written case-study / assignment work',
              'SUPPLEMENTARY': 'code, data, images and other supporting files', 'REFERENCE_LITERATURE': 'reference / literature lists',
              'COURSE_ADMINISTRATION': 'organisation, schedule, exam rules (extension)', 'TEMPLATE': 'layout templates (extension)',
              'DUPLICATE': 'byte-identical copy of another source (extension)',
              'SUPERSEDED_VERSION': 'older term edition of a lecture deck that exists in a newer edition; kept, never taught', 'SYSTEM_IGNORED': 'OS metadata / lock files (extension)',
              'OTHER_UNRESOLVED': 'not safely classifiable: kept, reported, may form a chapter only under review'}
CHAPTER_ROLES = {'ACADEMIC_CONTENT', 'REVIEW_REQUIRED'}
PAGED = {'.pdf', '.pptx'}
SUPPORT_FORMATS = {'.ipynb', '.py', '.r', '.sql', '.js', '.ts', '.c', '.cpp', '.h', '.java', '.sh', '.m', '.jl', '.rs', '.go',
                   '.csv', '.tsv', '.xlsx', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.tif', '.tiff', '.bmp', '.svg',
                   '.json', '.yaml', '.yml', '.xml', '.bib'}
ADMIN_RX = [re.compile(p, re.I) for p in (
    r'\bexam(ination)?\s+(date|registration|regulations?)\b|\bprüfungs(termin|anmeldung|ordnung)\b', r'\bbonus\b', r'\bgrade|\bnote\s*\d|\bnotenbonus',
    r'\b(ects|credit points?|leistungspunkte)\b', r'\b(ilias|moodle|canvas|stud\.?ip|olat)\b', r'\battendance|anwesenheit',
    r'\boffice hours?\b|\bsprechstunde', r'\broom\b|\bhörsaal|\braum\s+\d', r'[\w.-]+@[\w-]+\.[\w.]+', r'\bdeadline|\bfrist\b|\babgabe',
    r'\bregistration|\banmeldung|\bapplication (time|procedure|deadline)', r'\bschedule\b|\btermine?\b|\bdates?\b',
    r'\bcontact\b|\bkontakt\b', r'\bsubmission\b|\beinreichung', r'\b(mon|tue|wed|thu|fri)(day)?\b.*\b\d{1,2}[:.]\d{2}\b')]
TEMPLATE_RX = re.compile(r'sample (headline|text)|\b\d{1,2}\s?pt\b|lorem ipsum|click to (add|edit)|placeholder|platzhalter|'
                         r'insert (your|text|title)|text hier eingeben|^chapter heading$|^headline$|^subheadline$|your (name|title) here', re.I | re.M)
TEMPLATE_PATH = re.compile(r'templ(ate)?|vorlage|muster(?!lösung)', re.I)
PRACTICE_TITLE = re.compile(r'question catalog(ue)?|fragenkatalog|übungsfragen|practice (questions|problems)|review questions|'
                            r'self[- ]?test|selbsttest|quiz\b|wiederholungsfragen|exercise sheet|übungsblatt', re.I)
CASE_TITLE = re.compile(r'case stud(y|ies)|fallstudie', re.I)
# Written (student / project) work: title words plus authorship and paper-structure markers. Generic academic-writing
# vocabulary; not course- or file-specific.
WORK_TITLE = re.compile(r'case[\s_-]?stud(y|ies)|fallstudie|assignment|hausarbeit|seminar ?(paper|arbeit)|term paper|written submission|'
                        r'ausarbeitung|research brief|project report|projektbericht|thesis|bachelorarbeit|masterarbeit', re.I)
WORK_AUTHORSHIP = re.compile(r'\b(affidavit|declaration of (authorship|originality)|eidesstattlich\w*|selbstst(ä|ae)ndig\w* (verfasst|erkl)\w*|'
                             r'matrikel\w*|matriculation|student id|examiner|prüfer(in)?|supervisor|betreuer(in)?|submitted by|'
                             r'vorgelegt von|eingereicht von)\b', re.I)
WORK_STRUCTURE = re.compile(r'\b(table of contents?|inhaltsverzeichnis|list of (figures|tables|abbreviations)|abbildungsverzeichnis|'
                            r'tabellenverzeichnis|abkürzungsverzeichnis|bibliography|literaturverzeichnis|executive summary|'
                            r'research brief|abstract|appendix|anhang)\b', re.I)
ADMIN_TITLE = re.compile(r'\b(course|lecture|module|kurs|vorlesungs?|modul)?\s*(information|organi[sz]ation|orga\b|syllabus|'
                         r'modulhandbuch|course info|organisatorisches|formalities|formalia)', re.I)
NONCONTENT_TITLE = re.compile(r'^\s*(references?|literature|literatur(verzeichnis)?|sources?|quellen|bibliography|agenda|outline|'
                              r'gliederung|inhalt|contents?|overview|thank you|danke|questions\??|fragen\??|q\s*&\s*a|appendix|anhang|'
                              r'backup|imprint|disclaimer)\s*[:.!]?\s*$', re.I)
NUMBERED_Q = re.compile(r'^\s*(?:Q\s*)?(\d{1,3})[.)]\s+(\S.{8,})$')
CITATION = re.compile(r'^\s*\(?[A-Z][\w-]+( et al\.?| & [A-Z][\w-]+)?,? \(?\d{4}\)?|\bpos\.\s*\d+|\bp\.\s*\d+|\bdoi:|^\s*source\s*:|'
                      r'^\s*(inspired by|adapted from|nach|quelle)\b', re.I)
URL = re.compile(r'https?://|www\.', re.I)


def _norm(t):
    return re.sub(r'\s+', ' ', (t or '')).strip().lower()


def page_model(manifest):
    """{source_id: {'pages': {p: {...}}, 'boilerplate': set(norm texts), 'template_vector_counts': set}} for paged sources."""
    by = {e['element_id']: e for e in manifest['elements']}
    out = {}
    for s in manifest['sources']:
        if s['format'] not in PAGED:
            continue
        key = 'page' if s['format'] == '.pdf' else 'slide'
        pages = {}
        for i in s['element_ids']:
            e = by[i]; p = (e.get('locator') or {}).get(key)
            if p is None:
                continue
            pages.setdefault(p, []).append(e)
        n = len(pages) or 1
        occur, marginal = Counter(), Counter()
        for els in pages.values():
            H = max([((e.get('locator') or {}).get('bbox') or [0, 0, 0, 0])[3] for e in els] + [1])
            fs = [(e.get('structure') or {}).get('font_size') for e in els if isinstance((e.get('structure') or {}).get('font_size'), (int, float))]
            top = max(fs) if fs else None
            seen = set()
            for e in els:
                t = _norm(e['text'])
                if e['kind'] not in ('heading', 'paragraph') or not t or t in seen:
                    continue
                seen.add(t); occur[t] += 1
                bb = (e.get('locator') or {}).get('bbox') or [0, 0, 0, 0]
                f = (e.get('structure') or {}).get('font_size')
                # header/footer band or clearly smaller than the page's largest text: a running line, not a title
                if bb[1] >= 0.88 * H or bb[3] <= 0.08 * H or (top and isinstance(f, (int, float)) and f < 0.8 * top) or top is None:
                    marginal[t] += 1
        boiler = {t for t, c in occur.items() if c >= 3 and c >= 0.3 * n and marginal[t] >= 0.8 * c}
        vec = Counter((e.get('structure') or {}).get('vector_paths') for els in pages.values() for e in els if e['kind'] == 'diagram')
        template_vec = {k for k, c in vec.items() if k is not None and k <= 6 and c >= max(2, 0.15 * n)}
        img = Counter((e.get('asset') or {}).get('sha256') for els in pages.values() for e in els if e['kind'] == 'image')
        repeated_img = {h for h, c in img.items() if h and c >= 3}
        info = {}
        for p, els in pages.items():
            W = max([((e.get('locator') or {}).get('bbox') or [0, 0, 0, 0])[2] for e in els] + [1])
            H = max([((e.get('locator') or {}).get('bbox') or [0, 0, 0, 0])[3] for e in els] + [1])
            texts = [e for e in els if e['kind'] in ('heading', 'paragraph', 'list_item', 'table') and e['text'].strip()
                     and _norm(e['text']) not in boiler]
            info[p] = {'elements': els, 'text_chars': sum(len(e['text']) for e in texts), 'size': (W, H),
                       'title': _title(els, boiler, H), 'admin_hits': _admin_hits(' '.join(e['text'] for e in texts))}
        out[s['source_id']] = {'pages': info, 'boilerplate': boiler, 'template_vector_counts': template_vec,
                               'repeated_image_hashes': repeated_img, 'page_key': key}
    return out


def _title(els, boiler, H):
    cands = [e for e in els if e['kind'] in ('heading', 'paragraph') and _norm(e['text']) and _norm(e['text']) not in boiler
             and len(e['text']) <= 160]
    if not cands:
        return None
    heads = [e for e in cands if e['kind'] == 'heading' and (e.get('structure') or {}).get('placeholder') == 'title']
    if heads:
        return heads[0]
    top = [e for e in cands if ((e.get('locator') or {}).get('bbox') or [0, 0, 0, 0])[1] <= 0.35 * H] or cands
    sized = [e for e in top if isinstance((e.get('structure') or {}).get('font_size'), (int, float))]
    if sized:
        return max(sized, key=lambda e: (e['structure']['font_size'], -((e['locator'].get('bbox') or [0, 0])[1])))
    return next((e for e in top if e['kind'] == 'heading'), top[0])


def _admin_hits(text):
    return [rx.pattern[:40] for rx in ADMIN_RX if rx.search(text)]


def admin_page(info):
    return len(info['admin_hits']) >= 2


def source_roles(manifest, pm=None):
    pm = pm if pm is not None else page_model(manifest)
    by = {e['element_id']: e for e in manifest['elements']}
    roles = {}
    for s in manifest['sources']:
        ev = []
        if s.get('status') in ('ignored_metadata', 'ignored_temporary'):
            roles[s['source_id']] = {'source_id': s['source_id'], 'relative_path': s['relative_path'], 'role': 'SYSTEM_IGNORED',
                                     'confidence': 'HIGH', 'authority': s['authority'],
                                     'evidence': [{'signal': 'file_status', 'detail': s['status']}], 'note': 'never parsed'}
            continue
        dup = next((r['source_id'] for r in s.get('relationships', []) if r.get('kind') == 'duplicate_of'), None)
        if dup:
            roles[s['source_id']] = {'source_id': s['source_id'], 'relative_path': s['relative_path'], 'role': 'DUPLICATE',
                                     'confidence': 'HIGH', 'authority': s['authority'], 'duplicate_of': dup,
                                     'evidence': [{'signal': 'raw_sha256', 'detail': f'byte-identical to {dup}'}],
                                     'note': 'kept in the inventory; the first copy carries the content'}
            continue
        els = [by[i] for i in s['element_ids']]
        texts = [e for e in els if e['kind'] in ('heading', 'paragraph', 'list_item') and e['text'].strip()]
        path = s['relative_path']
        title_text = ' '.join(e['text'] for e in texts[:6])
        role, conf = None, 'MEDIUM'
        if s['format'] in SUPPORT_FORMATS:
            role, conf = 'SUPPORTING_MATERIAL', 'HIGH'; ev.append({'signal': 'format', 'detail': s['format']})
        elif s['authority'] == 'OFFICIAL_SOLUTION':
            role, conf = 'ASSESSMENT_SOLUTION', 'HIGH'; ev.append({'signal': 'authority', 'detail': s['authority_basis']})
        elif s['authority'] == 'OFFICIAL_EXAM':
            role, conf = 'ASSESSMENT_EXAM', 'HIGH'; ev.append({'signal': 'authority', 'detail': s['authority_basis']})
        elif s['authority'] == 'SUPPLEMENTARY' and re.search(r'literatur|reading', path, re.I):
            # textbooks/papers in a literature folder support the lecture; they never form chapters of their own
            role, conf = 'SUPPORTING_MATERIAL', 'HIGH'; ev.append({'signal': 'path', 'detail': 'supplementary literature folder'})
        if role is None:
            ph = [e for e in texts if TEMPLATE_RX.search(e['text'])]
            path_t = bool(TEMPLATE_PATH.search(path))
            if ph and (path_t or len(ph) >= 2):
                role, conf = 'TEMPLATE_LAYOUT', 'HIGH' if path_t and len(ph) >= 2 else 'MEDIUM'
                ev += [{'signal': 'placeholder_text', 'element_id': e['element_id'], 'locator': e['locator_str'], 'detail': e['text'][:60]} for e in ph[:5]]
                if path_t:
                    ev.append({'signal': 'file_name', 'detail': 'template/Vorlage token in path'})
            elif path_t:
                ev.append({'signal': 'file_name', 'detail': 'template token in path but no placeholder text'}); role = 'REVIEW_REQUIRED'
        if role is None:
            nq = sum(1 for e in texts for ln in e['text'].splitlines() if NUMBERED_Q.match(ln) and _is_question(ln))
            lines = sum(len(e['text'].splitlines()) for e in texts) or 1
            if PRACTICE_TITLE.search(path + ' ' + title_text) or s['authority'] == 'OFFICIAL_EXERCISE' or (nq >= 5 and nq >= 0.25 * lines):
                role, conf = 'PRACTICE_QUESTIONS', 'HIGH' if nq >= 5 else 'MEDIUM'
                ev.append({'signal': 'question_format', 'detail': f'{nq} numbered questions in {lines} lines'})
                if PRACTICE_TITLE.search(path + ' ' + title_text):
                    ev.append({'signal': 'title', 'detail': PRACTICE_TITLE.search(path + ' ' + title_text).group(0)})
        if role is None:
            if s['source_id'] in pm:
                pages = pm[s['source_id']]['pages']
                admin = [p for p, i in pages.items() if admin_page(i)]
                share = len(admin) / (len(pages) or 1)
                ev.append({'signal': 'admin_pages', 'detail': f'{len(admin)}/{len(pages)} pages with >=2 administration signals',
                           'pages': sorted(admin)[:20]})
            else:
                hits = _admin_hits(' '.join(e['text'] for e in texts))
                share = 1.0 if len(hits) >= 4 and len(texts) < 40 else 0.0
                ev.append({'signal': 'admin_terms', 'detail': f'{len(hits)} distinct administration signals'})
            case = bool(CASE_TITLE.search(path + ' ' + title_text))
            admin_title = ADMIN_TITLE.search(path + ' ' + title_text)
            if admin_title and share >= 0.1:
                ev.append({'signal': 'title', 'detail': f"administrative title '{admin_title.group(0).strip()}' with administration pages"})
                share = max(share, 0.5)
            full = '\n'.join(e['text'] for e in texts)
            work_title = WORK_TITLE.search(re.sub(r'[_\-]+', ' ', path) + ' ' + ' '.join(e['text'] for e in texts[:12]))
            authorship = sorted({m.group(0).lower() for m in WORK_AUTHORSHIP.finditer(full)})
            structure = sorted({m.group(0).lower() for m in WORK_STRUCTURE.finditer(full)})
            lines = [ln.strip() for e in texts for ln in e['text'].splitlines() if ln.strip()]
            cites = sum(1 for ln in lines if CITATION.search(ln) or re.search(r'\bdoi\b|https?://', ln, re.I))
            if share >= 0.5:
                role = 'CASE_STUDY_BRIEF' if case else 'COURSE_ADMINISTRATION'
                if case:
                    ev.append({'signal': 'title', 'detail': 'case study'})
            elif work_title and ((authorship and len(authorship) + len(structure) >= 2) or len(structure) >= 3):
                role, conf = 'CASE_STUDY_WORK', 'HIGH' if authorship and len(structure) >= 2 else 'MEDIUM'
                ev += [{'signal': 'title', 'detail': f"written-work title '{work_title.group(0)}'"},
                       {'signal': 'authorship_markers', 'detail': authorship},
                       {'signal': 'paper_structure_markers', 'detail': structure}]
            elif len(lines) >= 5 and cites >= 0.6 * len(lines):
                role = 'REFERENCE_LITERATURE'; ev.append({'signal': 'citation_lines', 'detail': f'{cites}/{len(lines)} lines are citations'})
            elif share >= 0.3:
                role = 'REVIEW_REQUIRED'; ev.append({'signal': 'mixed', 'detail': 'administration share between 30% and 50%'})
            elif case and share >= 0.15:
                role = 'REVIEW_REQUIRED'; ev.append({'signal': 'mixed', 'detail': 'case-study title with administration pages'})
            else:
                role = 'ACADEMIC_CONTENT'
        roles[s['source_id']] = {'source_id': s['source_id'], 'relative_path': path, 'role': role, 'confidence': conf,
                                 'authority': s['authority'], 'evidence': ev,
                                 'note': 'authority is not relevance; role decided from content/format signals'}
    _derived_work_pass(manifest, roles, by)
    _version_pass(manifest, roles, by)
    return roles


TERM = re.compile(r'\b(WS|WiSe|SS|SoSe|Winter(?:semester)?|Summer|Sommer(?:semester)?|Fall|Spring)\s*(?:term\s*)?(\d{4}|\d{2})(?:\s*/\s*(\d{4}|\d{2}))?', re.I)


def _term_key(text):
    """('WS2026/27' -> 2026.5, 'SS 2025' -> 2025.0); the latest term stated on the title pages, or None."""
    best = None
    for m in TERM.finditer(text):
        y = int(m.group(2)); y = y + 2000 if y < 100 else y
        k = y + (0.5 if m.group(1).lower().startswith(('ws', 'wi', 'fall')) else 0.0)
        best = k if best is None else max(best, k)
    return best


def _version_pass(manifest, roles, by):
    """Copies of one lecture deck (same file name without folder) that differ in content: when every copy states a
    distinct term (WS2025/26, WS2026/27 ...) on its first pages, the newest edition teaches and the others become
    SUPERSEDED_VERSION with the evidence. Without such evidence nothing is decided (both stay, flagged)."""
    groups = {}
    for s in manifest['sources']:
        if roles[s['source_id']]['role'] == 'ACADEMIC_CONTENT':
            groups.setdefault(s['relative_path'].rsplit('/', 1)[-1].lower(), []).append(s)
    for name, ss in groups.items():
        if len(ss) < 2:
            continue
        head = {s['source_id']: ' '.join(by[i]['text'] for i in s['element_ids'][:12]) for s in ss}
        terms = {sid: _term_key(t) for sid, t in head.items()}
        if None in terms.values() or len(set(terms.values())) != len(ss):
            for s in ss:
                roles[s['source_id']]['evidence'].append({'signal': 'version_variants', 'detail': f'{len(ss)} differing copies of {name}; '
                                                          'no distinct term on the title pages -> REVIEW: both taught'})
            continue
        newest = max(ss, key=lambda s: terms[s['source_id']])
        for s in ss:
            if s is newest:
                roles[s['source_id']]['evidence'].append({'signal': 'version_current', 'detail': f'newest term edition ({terms[s["source_id"]]})'})
                continue
            r = roles[s['source_id']]
            r.update(role='SUPERSEDED_VERSION', confidence='HIGH', superseded_by=newest['source_id'])
            r['evidence'].append({'signal': 'term_on_title_page', 'detail': f'term {terms[s["source_id"]]} < {terms[newest["source_id"]]} '
                                  f'of {newest["relative_path"]}'})


def _vocab(s, by):
    return set(re.findall(r'[a-zäöüß]{4,}', ' '.join(by[i]['text'] for i in s['element_ids']
                                                      if by[i]['kind'] in ('heading', 'paragraph', 'list_item', 'table')).lower()))


def _derived_work_pass(manifest, roles, by, min_share=0.6, margin=0.2):
    """B6.3 second pass: a source that looks like lecture material but whose vocabulary is mostly contained in a
    source already classified as written case-study / assignment work (e.g. the slides or an export of that work) is
    derived work, not a lecture. Needs a work signal in path or text; without it the source is REVIEW_REQUIRED with the
    evidence (never silently a lecture that could take a session)."""
    work = [s for s in manifest['sources'] if roles[s['source_id']]['role'] == 'CASE_STUDY_WORK']
    if not work:
        return
    lect = [s for s in manifest['sources'] if roles[s['source_id']]['role'] == 'ACADEMIC_CONTENT']
    voc = {s['source_id']: _vocab(s, by) for s in work + lect}
    for s in lect:
        v = voc[s['source_id']]
        if len(v) < 30:
            continue
        share = lambda o: len(v & voc[o['source_id']]) / len(v)
        best_w = max(work, key=share); w = share(best_w)
        jac = lambda o: len(v & voc[o['source_id']]) / (len(v | voc[o['source_id']]) or 1)
        # its own near-identical variants (e.g. a PDF export of the same slides) are no independent lecture evidence
        others = [share(o) for o in lect if o['source_id'] != s['source_id'] and jac(o) < 0.8]
        lmax = max(others, default=0.0)
        if w < min_share or w - lmax < margin:
            continue
        ev = {'signal': 'vocabulary_contained_in_case_study_work', 'detail': f"{w:.2f} of the vocabulary is in {best_w['relative_path']} "
              f"(best lecture {lmax:.2f})", 'derived_from': best_w['source_id']}
        texts = ' '.join(by[i]['text'] for i in s['element_ids'][:40])
        sig = WORK_TITLE.search(re.sub(r'[_\-]+', ' ', s['relative_path']) + ' ' + s['relative_path'] + ' ' + texts)
        r = roles[s['source_id']]
        if sig:
            r.update(role='CASE_STUDY_WORK', confidence='MEDIUM')
            r['evidence'] = r['evidence'] + [ev, {'signal': 'work_title', 'detail': sig.group(0)}]
        else:
            r.update(role='REVIEW_REQUIRED', confidence='LOW')
            r['evidence'] = r['evidence'] + [ev, {'signal': 'conflict', 'detail': 'lecture-like source mostly made of case-study '
                                                  'work vocabulary but without a work signal; review required'}]


def _shingles(text, k=5):
    w = re.findall(r'\w+', (text or '').lower())
    return {' '.join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}


def source_classification(manifest, roles):
    """B6.3: discovery result -> one category per source with evidence, plus near-duplicate / variant detection
    (word 5-gram Jaccard). Separate from curriculum mapping: chapters are formed only from OFFICIAL_LECTURE sources
    (and OTHER_UNRESOLVED under review); question linking uses EXERCISE_QUESTIONS sources."""
    by = {e['element_id']: e for e in manifest['elements']}
    out, sh = {}, {}
    for s in manifest['sources']:
        r = roles[s['source_id']]
        out[s['source_id']] = {'source_id': s['source_id'], 'relative_path': s['relative_path'], 'role': r['role'],
                               'category': CATEGORY_OF_ROLE.get(r['role'], 'OTHER_UNRESOLVED'), 'confidence': r.get('confidence'),
                               'evidence': r.get('evidence', []), 'variants': [],
                               **({'duplicate_of': r['duplicate_of']} if r.get('duplicate_of') else {}),
                               **({'superseded_by': r['superseded_by']} if r.get('superseded_by') else {})}
        if r['role'] not in ('SYSTEM_IGNORED', 'DUPLICATE'):
            t = ' '.join(by[i]['text'] for i in s['element_ids'] if by[i]['kind'] in ('heading', 'paragraph', 'list_item', 'table'))
            if len(t) >= 200:
                sh[s['source_id']] = _shingles(t)
    ids = sorted(sh)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            inter = len(sh[a] & sh[b])
            if not inter:
                continue
            j = inter / len(sh[a] | sh[b])
            if j >= 0.5:
                kind = 'NEAR_IDENTICAL_VARIANT' if j >= 0.8 else 'LIKELY_VARIANT'
                out[a]['variants'].append({'source_id': b, 'relative_path': out[b]['relative_path'], 'similarity': round(j, 3), 'kind': kind})
                out[b]['variants'].append({'source_id': a, 'relative_path': out[a]['relative_path'], 'similarity': round(j, 3), 'kind': kind})
    counts = {}
    for v in out.values():
        counts[v['category']] = counts.get(v['category'], 0) + 1
    return {'schema': 'em-source-classification-v1', 'categories': CATEGORIES, 'sources': out, 'counts': counts,
            'unresolved_source_ids': sorted(k for k, v in out.items() if v['category'] == 'OTHER_UNRESOLVED'),
            'rule': 'only OFFICIAL_LECTURE (and OTHER_UNRESOLVED, under review) form chapters; other categories stay in the '
                    'inventory and never take a session'}


QUESTION_VERB = re.compile(r'\?\s*$|^\s*(\d{1,3}[.)]\s*)?(what|why|how|which|who|when|where|name|explain|describe|define|give|list|'
                           r'compare|discuss|calculate|compute|derive|prove|fill|apply|was|warum|wie|welche|nennen|erkl|beschreib|'
                           r'definier|berechn|vergleich|leiten|beweis)', re.I)


def _is_question(line):
    return bool(QUESTION_VERB.search(line))


REJECT_REASONS = ('BOILERPLATE_REPEATED', 'TEMPLATE_PLACEHOLDER', 'NON_LEXICAL', 'CITATION_OR_SOURCE_LINE', 'URL_OR_EMAIL',
                  'CONTINUATION_FRAGMENT', 'NON_CONTENT_PAGE', 'ADMINISTRATIVE', 'TOO_LONG_FOR_TOPIC', 'DUPLICATE')


def candidate_reject(text, boiler=frozenset(), admin=False):
    """Why a heading/title line is not a competency candidate (None = acceptable candidate)."""
    t = (text or '').strip()
    n = _norm(t)
    if n in boiler:
        return 'BOILERPLATE_REPEATED'
    if TEMPLATE_RX.search(t):
        return 'TEMPLATE_PLACEHOLDER'
    letters = sum(ch.isalpha() for ch in t)
    if letters < 3 or letters < 0.5 * len(t.replace(' ', '')):
        return 'NON_LEXICAL'
    if URL.search(t) or re.search(r'[\w.-]+@[\w-]+\.', t):
        return 'URL_OR_EMAIL'
    if CITATION.search(t):
        return 'CITATION_OR_SOURCE_LINE'
    if NONCONTENT_TITLE.match(t) or re.match(r'^\s*(learning (objectives?|outcomes?)|lernziele?|ziele|objectives?)\s*[:.]?\s*$', t, re.I):
        return 'NON_CONTENT_PAGE'
    if admin or len(_admin_hits(t)) >= 1 and len(t) < 80:
        return 'ADMINISTRATIVE'
    if t[:1].islower() or t.endswith((',', '-', '–')) or t.startswith(('▪', '•', '…', '|', '/')) or \
            (t.startswith('(') and t.endswith(')')):   # '(Simplified) Example ...' is a title, '(€, thousand)' is not
        return 'CONTINUATION_FRAGMENT'
    if len(t) > 120:
        return 'TOO_LONG_FOR_TOPIC'
    return None


VISUAL_RULES = {
    'V0_TEMPLATE_VECTOR': 'vector drawing whose path count is the recurring page-template signature of this source '
                          '(<=6 paths on >=15% of pages): decoration candidate, non-blocking, sampled in review queue',
    'V0_REPEATED_IMAGE': 'identical raster (same SHA-256) on >=3 pages of the source: logo/decoration candidate, non-blocking',
    'V0_SMALL_IMAGE': 'raster covering <3% of the page area: decoration candidate, non-blocking',
    'V2_VISUAL_DOMINANT': 'page has < 200 characters of non-boilerplate text and a non-decorative visual: content lives in '
                          'the visual -> anchored competencies BLOCKED',
    'V1_LARGE_IMAGE': 'non-repeated raster covering >= 25% of a text page: relevance unknown -> REVIEW_REQUIRED',
    'V1_RELEVANCE_UNKNOWN': 'other non-decorative visual on a text page: relevance unknown -> REVIEW_REQUIRED (not READY)',
}


def visual_class(e, page_info, src_pm):
    """Return (class, rule) for an unresolved PDF visual."""
    W, H = page_info['size']; area = max(W * H, 1)
    bb = (e.get('locator') or {}).get('bbox')
    frac = ((bb[2] - bb[0]) * (bb[3] - bb[1]) / area) if bb else None
    if e['kind'] == 'diagram' and (e.get('structure') or {}).get('vector_paths') in src_pm['template_vector_counts']:
        return 'DECORATIVE_CANDIDATE', 'V0_TEMPLATE_VECTOR'
    if e['kind'] == 'image' and (e.get('asset') or {}).get('sha256') in src_pm['repeated_image_hashes']:
        return 'DECORATIVE_CANDIDATE', 'V0_REPEATED_IMAGE'
    if e['kind'] == 'image' and frac is not None and frac < 0.03:
        return 'DECORATIVE_CANDIDATE', 'V0_SMALL_IMAGE'
    if page_info['text_chars'] < 200:
        return 'ESSENTIAL', 'V2_VISUAL_DOMINANT'
    if e['kind'] == 'image' and frac is not None and frac >= 0.25:
        return 'RELEVANCE_UNKNOWN', 'V1_LARGE_IMAGE'
    return 'RELEVANCE_UNKNOWN', 'V1_RELEVANCE_UNKNOWN'
