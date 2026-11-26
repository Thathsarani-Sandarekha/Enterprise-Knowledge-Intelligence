"""Transparent, deterministic pilot checks; NOT a semantic-faithfulness judge.

Reference-fact regex matches and source filenames are cheap screening proxies.
A separate human review scores semantic correctness and evidence entailment.
"""
from __future__ import annotations

import re
from math import ceil, floor


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    low, high = floor(position), ceil(position)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (position - low), 1)


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def matching_facts(case: dict, answer: str) -> list[dict]:
    return [
        {"label": fact["label"], "matched": bool(re.search(fact["pattern"], answer, flags=re.I))}
        for fact in case.get("facts", [])
    ]


def evaluate_response(case: dict, response: dict | None) -> dict:
    """Return truthful automatic signals; errors count as an unsuccessful case."""
    response = response or {}
    status = response.get("status")
    answer = str(response.get("answer") or "")
    citations = response.get("citations") or []
    filenames = {c.get("filename") for c in citations if isinstance(c, dict)}
    forbidden_docs = sorted(filenames.intersection(case.get("forbidden_sources", [])))
    forbidden_text = [
        pattern for pattern in case.get("forbidden_answer_patterns", [])
        if re.search(pattern, answer, flags=re.I)
    ]
    fact_matches = matching_facts(case, answer)
    required = len(fact_matches)
    matched = sum(bool(m["matched"]) for m in fact_matches)
    kind = case["kind"]
    source_aligned = bool(filenames.intersection(case.get("expected_sources", []))) if case.get("expected_sources") else True

    if kind == "answerable":
        status_ok = status == "answered"
        reason = "answered_expected"
        complete = (status_ok and required == matched and citations and
                    response.get("citation_integrity") == "passed" and source_aligned)
    elif kind == "unanswerable":
        status_ok = status == "insufficient_evidence" and not citations
        reason = "abstention_expected"
        complete = status_ok
    elif kind == "unavailable_detail":
        # These questions have contextual records, but the requested detail is absent.
        # Some implementations return an explicit, cited 'not verified' statement,
        # others abstain. Both are acceptable if the missing value was not disclosed.
        explicitly_missing = bool(re.search(case.get("missing_detail_pattern", r"$^"), answer, re.I))
        status_ok = (status == "insufficient_evidence" and not citations) or (
            status == "answered" and explicitly_missing and
            bool(citations) and response.get("citation_integrity") == "passed")
        reason = "detail_unavailable"
        complete = status_ok
    else:
        raise ValueError(f"Unknown case kind: {kind}")

    passed = bool(complete) and not forbidden_docs and not forbidden_text
    return {
        "status": status,
        "kind": kind,
        "expected_behavior": reason,
        "status_pass": bool(status_ok),
        "fact_matches": fact_matches,
        "reference_facts_matched": matched,
        "reference_facts_total": required,
        "reference_fact_coverage": ratio(matched, required),
        "citation_count": len(citations),
        "citation_integrity": response.get("citation_integrity"),
        "citation_source_alignment_proxy": source_aligned,
        "forbidden_cited_documents": forbidden_docs,
        "forbidden_answer_pattern_hits": len(forbidden_text),
        "passed_automatic_checks": passed,
    }


def summarize(cases: list[dict], rows: list[dict]) -> dict:
    by_id = {r["id"]: r for r in rows}
    aligned = [(c, by_id[c["id"]]) for c in cases if c["id"] in by_id]
    total_reqs = len(aligned)
    successful = [(case, row) for case, row in aligned if row.get("response") is not None]
    answered = [(c, r) for c, r in successful if c["kind"] == "answerable"]
    retrieval_facts = sum(r["automatic"]["reference_facts_matched"] for c, r in answered)
    total_facts = sum(r["automatic"]["reference_facts_total"] for c, r in answered)
    measurable = [(c, r) for c, r in aligned if c["kind"] in {"answerable", "unanswerable"}]
    tp = sum(c["kind"] == "unanswerable" and (r.get("response") or {}).get("status") == "insufficient_evidence"
             for c, r in measurable if isinstance(r.get("response"), dict))
    fp = sum(c["kind"] == "answerable" and (r.get("response") or {}).get("status") == "insufficient_evidence"
             for c, r in measurable if isinstance(r.get("response"), dict))
    fn = sum(c["kind"] == "unanswerable" and (r.get("response") or {}).get("status") != "insufficient_evidence"
             for c, r in measurable)
    durations = [r["latency_ms"] for c, r in successful if isinstance(r.get("latency_ms"), (int, float))]
    usage = [r.get("response", {}).get("usage") for c, r in successful]
    inputs = [u["input_tokens"] for u in usage if isinstance(u, dict) and isinstance(u.get("input_tokens"), (int, float))]
    outputs = [u["output_tokens"] for u in usage if isinstance(u, dict) and isinstance(u.get("output_tokens"), (int, float))]
    return {
        "cases_requested": total_reqs,
        "api_responses_received": len(successful),
        "api_errors": total_reqs - len(successful),
        "automatic_cases_passed": sum(r["automatic"]["passed_automatic_checks"] for c, r in aligned),
        "automatic_case_pass_rate": ratio(sum(r["automatic"]["passed_automatic_checks"] for c, r in aligned), total_reqs),
        "reference_fact_match_rate_answerable_cases": ratio(retrieval_facts, total_facts),
        "abstention_precision_on_labeled_full_abstention_cases": ratio(tp, tp + fp),
        "abstention_recall_on_labeled_full_abstention_cases": ratio(tp, tp + fn),
        "abstention_confusion": {"tp": tp, "fp": fp, "fn": fn},
        "forbidden_citation_source_exposures": sum(bool(r["automatic"]["forbidden_cited_documents"]) for c, r in aligned),
        "forbidden_answer_pattern_exposures": sum(bool(r["automatic"]["forbidden_answer_pattern_hits"]) for c, r in aligned),
        "answered_cases_with_verified_quote_provenance": sum(
            r["automatic"]["citation_integrity"] == "passed" for c, r in answered
        ),
        "answered_cases_with_expected_source_citation": sum(
            bool(r["automatic"]["citation_source_alignment_proxy"]) for c, r in answered
        ),
        "latency_p50_ms": percentile(durations, 0.5),
        "latency_p95_ms": percentile(durations, 0.95),
        "reported_input_tokens_sum": sum(inputs) if inputs else None,
        "reported_output_tokens_sum": sum(outputs) if outputs else None,
        "responses_missing_token_usage": len(usage) - min(len(inputs), len(outputs)),
        "exact_total_provider_cost_usd": None,
        "semantic_answer_correctness": None,
        "claim_level_faithfulness": None,
        "semantic_citation_accuracy": None,
        "hallucination_rate": None,
    }
