"""Unit checks; no Groq requests or model downloads."""
from app.services.fusion import fused_ids
from app.services.answers import DraftAnswer, verify_draft, abstention
from app.services.retrieval import Evidence, keyword_expression


def make_evidence():
    return Evidence(
        chunk_id='chunk-1', document_id='doc-1', filename='hospitality_quote.xlsx',
        project_code='SOL-2025', text='A12=FR-220 fire-rated upholstery; B12=$145/yard',
        source={'format': 'xlsx', 'cell_range': "'Materials'!A12:B12"},
        rrf_score=.025, rerank_score=3.2,
    )


def test_valid_citation_uses_db_source():
    draft = DraftAnswer(status='answered', answer='FR-220 is quoted at $145/yard.',
                        citations=[{'evidence_id': 'E1', 'quote': 'FR-220 fire-rated upholstery'}])
    valid, citations = verify_draft(draft, [make_evidence()])
    assert valid
    assert citations[0]['source']['cell_range'] == "'Materials'!A12:B12"


def test_unknown_source_and_fabricated_quote_are_rejected():
    fabricated = DraftAnswer(status='answered', answer='Something',
                             citations=[{'evidence_id': 'E1', 'quote': '$9999 per yard'}])
    wrong_id = DraftAnswer(status='answered', answer='Something',
                           citations=[{'evidence_id': 'E9', 'quote': 'FR-220 fire-rated upholstery'}])
    assert not verify_draft(fabricated, [make_evidence()])[0]
    assert not verify_draft(wrong_id, [make_evidence()])[0]


def test_no_evidence_abstains():
    result = abstention('no_accessible_evidence')
    assert result['status'] == 'insufficient_evidence'
    assert result['citations'] == []


def test_keyword_terms_do_not_become_unsafe_sql():
    terms = keyword_expression('Find fire-rated upholstery with supplier prices; DROP TABLE docs;')
    assert ';' not in terms
    assert 'fire' in terms


def test_multiple_quotes_from_same_evidence():
    draft = DraftAnswer(
        status="answered",
        answer="FR-220 was quoted at $145 per yard.",
        citations=[
            {
                "evidence_id": "E1",
                "quote": "FR-220 fire-rated upholstery"
            },
            {
                "evidence_id": "E1",
                "quote": "B12=$145/yard"
            }
        ]
    )

    valid, citations = verify_draft(
        draft,
        [make_evidence()]
    )

    assert valid is True
    assert len(citations) == 2
    assert all(c["chunk_id"] == "chunk-1" for c in citations)
