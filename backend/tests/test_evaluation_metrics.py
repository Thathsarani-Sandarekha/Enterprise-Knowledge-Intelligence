from evaluation.metrics import recall_at_k, reciprocal_rank_at_k, percentile_nearest_rank, summarize


def test_recall_is_document_level_and_not_inflated_by_repeated_chunks():
    ranked = ['a.pdf', 'a.pdf', 'b.docx']
    assert recall_at_k(ranked, ['a.pdf', 'b.docx'], 3) == 1.0
    assert recall_at_k(ranked, ['a.pdf', 'b.docx'], 2) == 0.5


def test_reciprocal_rank_uses_first_relevant_chunk():
    assert reciprocal_rank_at_k(['wrong.pdf', 'right.pdf', 'right.pdf'], ['right.pdf'], 3) == 0.5
    assert reciprocal_rank_at_k(['wrong.pdf'], ['right.pdf'], 1) == 0.0


def test_unanswerable_cases_are_not_counted_as_failed_retrieval():
    assert recall_at_k([], [], 5) is None
    assert reciprocal_rank_at_k([], [], 5) is None


def test_nearest_rank_95th():
    assert percentile_nearest_rank([10, 20, 30, 40, 50], .95) == 50


def test_security_violations_counted_separately():
    records = [dict(method='keyword', recall_at_k=None, reciprocal_rank_at_k=None,
                    latency_ms=10.0, expected_empty=True, ranked_filenames=['leak.pdf'],
                    forbidden_returned=['leak.pdf'])]
    summary = summarize(records, 'keyword')
    assert summary['forbidden_document_exposures'] == 1
    assert summary['expected_empty_violations'] == 1
    assert summary['answerable_queries'] == 0
