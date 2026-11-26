"""Semantic graphics projected through the existing figures_svg renderer.

The interaction variants are the canonical parameter/state store. A graphic
names meaningful objects, claims, placements and reproducible keyframes;
no arbitrary SVG/HTML is accepted from a learning-unit file.
"""
from .. import figures_svg


def specifications(unit):
    interactions = {i['id']:i for i in unit['interactions']}
    teaching = {i['id'] for i in unit['teaching']}
    tasks = {i['id'] for i in unit['assessments']}
    claims = {i['id'] for i in unit['claims']}
    skills = {i['id'] for i in unit['competencies']}
    seen, result = set(), []
    for item in unit.get('graphics', []):
        required = {'id','model_ref','interaction_id','teaching_id','assessment_ids','claim_ids','competency_ids','objects','keyframes','alt','caption'}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError('graphic: exact semantic graphic fields required')
        from .experience import SEMANTIC_ID
        if not isinstance(item['id'],str) or not SEMANTIC_ID.fullmatch(item['id']) or item['id'] in seen:
            raise ValueError('graphic: unique semantic ID required')
        seen.add(item['id'])
        interaction = interactions.get(item['interaction_id'])
        if not interaction or item['model_ref'] != interaction['model_ref'] or item['model_ref'] not in {'binomial_area_partition','scaled_dot_product_attention'}:
            raise ValueError('graphic: model/interaction mismatch')
        for field, known in [('claim_ids',claims),('competency_ids',skills),('assessment_ids',tasks)]:
            if not isinstance(item[field],list) or not item[field] or not set(item[field]) <= known:
                raise ValueError('graphic: unresolved ' + field)
        if item['teaching_id'] not in teaching: raise ValueError('graphic: unresolved teaching placement')
        for field in ('alt','caption'):
            if not isinstance(item[field],str) or not item[field].strip(): raise ValueError('graphic: meaningful '+field+' required')
        if (not isinstance(item['objects'],dict) or not item['objects'] or
                any(not isinstance(v,str) or not v.strip() for v in item['objects'].values())):
            raise ValueError('graphic: visual object meanings required')
        frames = item['keyframes']
        if not isinstance(frames,list) or not 1 <= len(frames) <= 6 or len(set(map(str,frames))) != len(frames):
            raise ValueError('graphic: 1..6 unique keyframes required')
        for index in frames:
            if type(index) is not int or not 0 <= index < len(interaction['variants']):
                raise ValueError('graphic: unknown interactive state')
            variant = interaction['variants'][index]
            spec = {'type':item['model_ref'],'parameters':variant['parameters'],
                    'title':item['caption'],'alt':item['alt']}
            # Rendering validates the trusted mathematical model as well.
            figures_svg.render(spec)
            result.append((item, index, spec))
    return result


def html_frames(unit, teaching_id):
    from html import escape
    result = []
    for item, index, spec in specifications(unit):
        if item['teaching_id'] == teaching_id:
            result.append('<figure class="semantic-figure" data-graphic-id="'+escape(item['id'])+'">'+
                figures_svg.render(spec)+'<figcaption>'+escape(item['caption'])+
                ' · Zustand '+str(index+1)+'. '+escape(item['alt'])+'</figcaption></figure>')
    return ''.join(result)
