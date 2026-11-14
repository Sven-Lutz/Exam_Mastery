"""G0 accepts exactly the provenance values the author block schema allows (SOURCE_PARAPHRASE was rejected by G0)."""
from exam_mastery import role_schemas, validate


def test_g0_provenance_matches_author_block_schema():
    assert set(role_schemas.BLOCK['properties']['provenance']['enum']) == validate.PROVENANCE
