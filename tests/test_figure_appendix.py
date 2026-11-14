"""Figure appendix (6_Quellenabbildungen.pdf): status per page from the imported readings, chapter decks only, sorted."""
import pymupdf
import pytest

from exam_mastery.chapter_publish import publish_visual_sources


def _png(path):
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 8, 6), 0)
    pix.clear_with(200)
    pix.save(str(path))


@pytest.fixture
def setup(tmp_path):
    (tmp_path / 'img').mkdir()
    els, renders = [], []
    for sid, page in [('src-a', 3), ('src-a', 1), ('src-a', 2), ('src-b', 7)]:
        _png(tmp_path / 'img' / f'{sid}-{page}.png')
        els.append({'element_id': f'r-{sid}-{page}', 'kind': 'rendered_page', 'source_id': sid, 'locator': {'page': page},
                    'asset': {'path': f'img/{sid}-{page}.png'}})
        els.append({'element_id': f't-{sid}-{page}', 'kind': 'text', 'source_id': sid, 'locator': {'page': page}})
    manifest = {'elements': els, 'sources': [{'source_id': 'src-a', 'relative_path': 'Deck A.pdf'},
                                             {'source_id': 'src-b', 'relative_path': 'Other lecture.pdf'}]}
    ctx = {'competencies': [
        # competency says "text only", but page 2 has an accepted reading -> page status must say evaluated
        {'statement': 'k1', 'auto_scope': {'basis': 'AUTO_TEXT_ONLY'}, 'source_anchor_ids': ['t-src-a-2', 't-src-a-1', 't-src-b-7']},
        # competency says "vision transcribed", but page 3 has no reading -> must not claim evaluated
        {'statement': 'k2', 'auto_scope': {'basis': 'AUTO_VISION_TRANSCRIBED'}, 'source_anchor_ids': ['t-src-a-3']},
    ]}
    evidence = {'pages': [{'source_id': 'src-a', 'page': 2, 'statements': [{'text': 'x'}]}]}
    return tmp_path, manifest, ctx, evidence


def _pages(pdf):
    return [p.get_text() for p in pymupdf.open(pdf)][1:]


def test_status_follows_reading_and_other_decks_are_dropped(setup):
    tmp, manifest, ctx, ev = setup
    n = publish_visual_sources(ctx, manifest, tmp, tmp / 'f.pdf', chapter_sources=['src-a'], evidence=ev)
    assert n == 3
    pages = _pages(tmp / 'f.pdf')
    assert [p.splitlines()[0] for p in pages] == ['Deck A.pdf, S. 1', 'Deck A.pdf, S. 2', 'Deck A.pdf, S. 3']
    assert 'vom Agenten ausgewertet' in pages[1]
    assert 'vom Agenten ausgewertet' not in pages[0]
    assert 'Other lecture' not in ''.join(pages)


def test_cover_counts_match_pages(setup):
    tmp, manifest, ctx, ev = setup
    publish_visual_sources(ctx, manifest, tmp, tmp / 'f.pdf', chapter_sources=['src-a'], evidence=ev)
    cover = ' '.join(pymupdf.open(tmp / 'f.pdf')[0].get_text().split())
    assert '1 Folien: Abbildung vom Agenten ausgewertet' in cover


def test_without_chapter_sources_the_dominant_deck_is_used(setup):
    tmp, manifest, ctx, ev = setup
    publish_visual_sources(ctx, manifest, tmp, tmp / 'f.pdf', evidence=ev)
    assert 'Other lecture' not in ''.join(_pages(tmp / 'f.pdf'))
