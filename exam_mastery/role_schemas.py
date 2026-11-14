"""JSON schemas for structured output of the chapter roles (B6.8), written from the role prompts' output contracts.

They constrain the SHAPE only (types, required keys, enums); the existing contract validators and quality gates still
decide what is acceptable. Free-form parts (figure specs, decision payloads, rubric extras) stay open objects.
Only JSON-Schema keywords in the Gemini subset are used: type, properties, required, items, enum, description,
additionalProperties.
"""
S, I, N, B = {'type': 'string'}, {'type': 'integer'}, {'type': 'number'}, {'type': 'boolean'}
OPEN = {'type': 'object', 'additionalProperties': True}
STRS = {'type': 'array', 'items': S}
STEP = {'type': 'object', 'properties': {'statement': S, 'justification': S, 'element': S, 'fact': S}, 'required': ['statement']}


def obj(props, required=(), extra=False):
    o = {'type': 'object', 'properties': props, 'required': list(required)}
    if extra:
        o['additionalProperties'] = True
    return o


def arr(item):
    return {'type': 'array', 'items': item}


BLOCK = obj({'block_id': S, 'kind': S, 'kc_ids': STRS, 'title': S, 'body': S, 'steps': arr(STEP), 'source_refs': STRS,
             'external_refs': STRS, 'provenance': {'type': 'string', 'enum': ['COURSE_SOURCE', 'SOURCE_PARAPHRASE', 'AUTHOR_INFERENCE',
                                                                              'VERIFIED_SUPPLEMENT', 'AUTHOR_CREATED', 'EXAM_ADAPTED']},
             'claim_support_status': S, 'norm_refs': STRS, 'shape_checks': OPEN, 'problem': S, 'result': S, 'interpretation': S,
             'assumptions': STRS, 'rubric': STRS, 'typical_errors': STRS},
            ['block_id', 'kind', 'kc_ids', 'provenance', 'claim_support_status'], extra=True)
FIGURE = obj({'figure_id': S, 'purpose': S, 'didactic_rationale': S, 'source_element_id': S, 'source_element_ids': STRS,
              'status': {'type': 'string', 'enum': ['SOURCE_ASSET_REUSED', 'REDRAW_FROM_SOURCE_SPEC', 'OPEN_NOT_GENERATED']},
              'linked_block_ids': STRS, 'answers_item_ids': STRS, 'caption': S, 'alt_text': S, 'review_status': S,
              'necessity': {'type': 'string', 'enum': ['ESSENTIAL', 'SUPPLEMENTARY']}, 'spec': OPEN},
             ['figure_id', 'status'], extra=True)
ISSUE = obj({'issue_id': S, 'object_id': S, 'code': S, 'detail': S}, ['code', 'detail'])
EXAM_ANSWER = obj({'item_id': S, 'answer': S, 'answer_points': STRS, 'source_refs': STRS,
                   'status': {'type': 'string', 'enum': ['ANSWERED_FROM_SOURCE', 'SOURCE_MISSING', 'SUPPLEMENT_REQUIRED']},
                   'supplement': obj({'text': S, 'external_refs': STRS})}, ['item_id', 'status'])
AUTHOR = obj({'learning_objectives': arr(obj({'kc_id': S, 'statement': S, 'operations': STRS}, ['kc_id', 'statement'])),
              'notation': arr(obj({'notation_id': S, 'symbol': S, 'meaning': S, 'status': S, 'resolution': OPEN}, ['symbol', 'meaning'])),
              'blocks': arr(BLOCK), 'figures': arr(FIGURE), 'open_issues': arr(ISSUE), 'exam_answers': arr(EXAM_ANSWER)},
             ['learning_objectives', 'notation', 'blocks', 'figures', 'open_issues', 'exam_answers'])
ITEM = obj({'item_id': S, 'kc_ids': STRS, 'prompt': S, 'format': S, 'difficulty': S, 'required_operation': S, 'points': N,
            'transfer_relation': S, 'exam_link_item_ids': STRS, 'source_refs': STRS, 'refers_to_block_ids': STRS, 'solution_id': S,
            'actual_operation_review': S, 'target': obj({'kind': S, 'text': S}, ['kind', 'text']),
            'variation': obj({'from_ref': S, 'changed': STRS}), 'given_data': OPEN},
           ['item_id', 'kc_ids', 'prompt', 'difficulty', 'solution_id'], extra=True)
ASSESSMENT = obj({'assessments': arr(ITEM)}, ['assessments'])
SOLUTION = obj({'solution_id': S, 'item_id': S, 'steps': arr(STEP), 'answer': S, 'alternatives': STRS, 'hint_ladder': STRS,
                'rubric': arr(obj({'criterion': S, 'points': N, 'evidence_of': S}, ['criterion', 'points'])), 'typical_errors': STRS,
                'numeric_checks': arr(obj({'expression': S, 'expected': N}, ['expression', 'expected'])),
                'tests': arr(OPEN)}, ['solution_id', 'item_id', 'steps', 'answer'], extra=True)
SOLUTIONS = obj({'solutions': arr(SOLUTION)}, ['solutions'])
FINDING = obj({'severity': {'type': 'string', 'enum': ['blocker', 'major', 'minor', 'info']}, 'description': S, 'object_id': S},
              ['severity', 'description'])
REVIEW = obj({'schema': {'type': 'string', 'enum': ['em-semantic-decisions-v1']}, 'decisions': arr(OPEN),
              'claim_reviews': arr(obj({'block_id': S, 'verdict': {'type': 'string', 'enum': ['SUPPORTED', 'UNSUPPORTED', 'UNCLEAR']},
                                        'rationale': S, 'element_ids': STRS}, ['block_id', 'verdict'])),
              'findings': arr(FINDING)}, ['schema', 'decisions', 'claim_reviews', 'findings'])
RISK = obj({'verdict': {'type': 'string', 'enum': ['PASS', 'FAIL', 'NEEDS_REVIEW']}, 'findings': arr(FINDING)}, ['verdict', 'findings'])
REVISION = obj({'blocks': arr(BLOCK), 'assessments': arr(ITEM), 'solutions': arr(SOLUTION), 'figures': arr(FIGURE)},
               ['blocks', 'assessments', 'solutions', 'figures'])

SCHEMAS = {'chapter_author': AUTHOR, 'chapter_assessment': ASSESSMENT, 'chapter_solutions': SOLUTIONS,
           'chapter_semantic_review': REVIEW, 'chapter_risk_review': RISK, 'chapter_revision': REVISION}


def schema_for(role):
    """Schema for a chapter role, or None (legacy roles fall back to JSON mode without a schema)."""
    return SCHEMAS.get(role)
