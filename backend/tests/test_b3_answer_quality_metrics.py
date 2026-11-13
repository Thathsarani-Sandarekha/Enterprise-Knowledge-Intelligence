"""Offline tests: no FastAPI, database, or Groq calls required."""
from evaluation.answer_quality_metrics import evaluate_response, summarize, percentile
from scripts.score_answer_reviews import score_manual_reviews
import pytest


def test_percentile_uses_linear_interpolation():
    assert percentile([10, 20, 30, 40], 0.5) == 25
    assert percentile([], 0.95) is None


def test_answerable_case_proxy_requires_real_source_and_reference_fact():
    case = {'id': 'A', 'role': 'aster-procurement', 'kind': 'answerable',
            'facts': [{'label': 'item', 'pattern': r'UPH-FR-220'}],
            'expected_sources': ['quotes.xlsx']}
    response = {'status': 'answered', 'answer': 'UPH-FR-220 approved.',
                'citation_integrity': 'passed',
                'citations': [{'filename': 'quotes.xlsx', 'supporting_quote': 'UPH-FR-220'}]}
    score = evaluate_response(case, response)
    assert score['passed_automatic_checks']
    assert score['reference_fact_coverage'] == 1.0
    response['citations'] = [{'filename': 'wrong.pdf'}]
    assert not evaluate_response(case, response)['passed_automatic_checks']


def test_missing_detail_may_abstain_or_explain_without_leaking_price():
    case = {'kind': 'unavailable_detail', 'facts': [],
            'forbidden_sources': ['private.xlsx'],
            'missing_detail_pattern': 'unavailable',
            'forbidden_answer_patterns': [r'\$145']}
    abstain = {'status': 'insufficient_evidence', 'citations': [], 'answer': 'Cannot verify.'}
    assert evaluate_response(case, abstain)['passed_automatic_checks']
    partial = {'status': 'answered', 'answer': 'The price is unavailable.',
               'citations': [{'filename': 'public.docx'}], 'citation_integrity': 'passed'}
    assert evaluate_response(case, partial)['passed_automatic_checks']
    partial['answer'] = 'The price is $145.'
    assert not evaluate_response(case, partial)['passed_automatic_checks']


def test_abstention_precision_and_recall_scored_only_on_labeled_cases():
    cases = [{'id':'A','kind':'answerable'}, {'id':'B','kind':'unanswerable'},
             {'id':'C','kind':'unavailable_detail'}]
    mk = lambda id, status: {'id':id, 'response':{'status':status},
                             'automatic': {'passed_automatic_checks': True,
                              'reference_facts_matched':0, 'reference_facts_total':0,
                              'forbidden_cited_documents':[],
                              'forbidden_answer_pattern_hits':0,
                              'citation_integrity':'not_applicable',
                              'citation_source_alignment_proxy':True},
                             'latency_ms':12.0}
    scores = summarize(cases, [mk('A','answered'),mk('B','insufficient_evidence'),
                               mk('C','answered')])
    assert scores['abstention_precision_on_labeled_full_abstention_cases'] == 1.0
    assert scores['abstention_recall_on_labeled_full_abstention_cases'] == 1.0


def test_error_response_does_not_crash_summarizer():
    case = {'id':'A','kind':'unanswerable'}
    row = {'id':'A','response':None,'automatic':evaluate_response(case,None),
           'latency_ms': 100.0}
    scores = summarize([case], [row])
    assert scores['api_errors'] == 1
    assert scores['abstention_recall_on_labeled_full_abstention_cases'] == 0.0


def test_manual_review_refuses_to_invent_scores():
    result = score_manual_reviews([{'id':'A','reviewed':False,'overall_correct':None,'claims':[]}])
    assert result['case_level_answer_correctness_reviewed'] is None
    assert result['claim_level_faithfulness_reviewed'] is None


def test_manual_review_claim_counts():
    result = score_manual_reviews([{
        'id':'A','reviewed':True,'response_status':'answered',
        'overall_correct':False,
        'claims':[{'claim':'Material A is approved','supported':True,'citation_supports':True},
                  {'claim':'Certified by third party','supported':False,'citation_supports':False}],
    }])
    assert result['claim_level_faithfulness_reviewed'] == 0.5
    assert result['unsupported_claim_count'] == 1
    assert result['claim_level_citation_support_reviewed'] == 0.5


def test_review_requires_all_claims_annotated():
    with pytest.raises(ValueError):
        score_manual_reviews([{'id':'A','reviewed':True,'response_status':'answered',
                               'overall_correct':True,'claims':[]}])
