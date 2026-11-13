"""No Groq calls or database writes. Exercises the existing answer verifier."""
import pytest

from app.services.answers import DraftAnswer, verify_draft, generate_answer
from app.services.retrieval import Evidence


def evidence():
    return [Evidence(
        chunk_id='test-chunk', document_id='test-doc',
        filename='synthetic_finish_approvals.docx', project_code='SGR-2025',
        text='UPH-FR-220 was approved for Solstice Grand Resort. '
             'Supplier Northstar Contract Textiles provided dossier FR-DOC-220.',
        source={'section': 'Synthetic approval'}, rrf_score=0.0, rerank_score=0.0,
    )]


def draft(citations, status='answered'):
    return DraftAnswer(status=status,
                       answer='UPH-FR-220 was approved for the resort.',
                       citations=citations)


def test_valid_verbatim_quote_accepted():
    ok, verified = verify_draft(draft([{'evidence_id': 'E1',
        'quote': 'UPH-FR-220 was approved for Solstice Grand Resort.'}]), evidence())
    assert ok and verified[0]['document_id'] == 'test-doc'


def test_unknown_source_id_rejected():
    ok, verified = verify_draft(draft([{'evidence_id': 'E99',
        'quote': 'UPH-FR-220 was approved for Solstice Grand Resort.'}]), evidence())
    assert not ok and verified == []


def test_fabricated_quote_rejected():
    ok, verified = verify_draft(draft([{'evidence_id': 'E1',
        'quote': 'UPH-FR-220 has certified Class A performance.'}]), evidence())
    assert not ok and verified == []


def test_duplicate_evidence_id_valid_for_different_excerpts():
    # This regression corresponds to the duplicate-E2 failure fixed in Task 4.
    ok, verified = verify_draft(draft([
        {'evidence_id': 'E1', 'quote': 'UPH-FR-220 was approved for Solstice Grand Resort.'},
        {'evidence_id': 'E1', 'quote': 'Supplier Northstar Contract Textiles provided dossier FR-DOC-220.'},
    ]), evidence())
    assert ok and len(verified) == 2


def test_insufficient_evidence_cannot_cite_sources():
    d = draft([{'evidence_id': 'E1', 'quote': 'UPH-FR-220 was approved for Solstice Grand Resort.'}],
              status='insufficient_evidence')
    ok, verified = verify_draft(d, evidence())
    assert not ok and verified == []


def test_no_evidence_abstains_without_groq(monkeypatch):
    # The external provider must never be contacted when retrieval is empty.
    import app.services.answers as answers
    monkeypatch.setattr(answers, 'get_groq',
                        lambda: pytest.fail('Groq must not be called for empty evidence'))
    result = generate_answer('Tell me about an inaccessible hotel record', [], {})
    assert result['status'] == 'insufficient_evidence'
    assert result['citations'] == []
