"use client";

import { FormEvent, useState } from "react";
import {
  ArrowUpRight, BookOpenText, ChevronRight, Clock3, FileSearch,
  FileText, Layers3, LoaderCircle, MessageSquareText, Search, ShieldCheck,
  Sparkles, WandSparkles,
} from "lucide-react";
import { request, humanSource } from "@/lib/api";
import type { AnswerResponse, Citation, DemoUser, SearchResponse } from "@/lib/api";

type Mode = "ask" | "search";
const examples = [
  "Find fire-rated upholstery approved in previous hotel renovations, including suppliers and quoted prices.",
  "Which materials were approved for the Saint George renovation?",
  "Find supplier quotations for hospitality upholstery and lead times.",
];

export function KnowledgeSearch({ user, onOpenLibrary }: { user: DemoUser; onOpenLibrary: () => void }) {
  const [question, setQuestion] = useState("");
  const [project, setProject] = useState("");
  const [mode, setMode] = useState<Mode>("ask");
  const [answer, setAnswer] = useState<AnswerResponse | null>(null);
  const [search, setSearch] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(e?: FormEvent) {
    e?.preventDefault();
    if (question.trim().length < 5 || loading) return;
    setError(null);
    setLoading(true);
    setAnswer(null);
    setSearch(null);
    try {
      const body = JSON.stringify({ question: question.trim(), top_k: 6, ...(project.trim() ? { project_code: project.trim() } : {}) });
      if (mode === "ask") {
        setAnswer(await request<AnswerResponse>("knowledge/ask", user, { method: "POST", body }));
      } else {
        setSearch(await request<SearchResponse>("knowledge/search", user, { method: "POST", body }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally { setLoading(false); }
  }


  const retrieval = answer?.retrieval || search?.retrieval;
  const hasResponse = !!answer || !!search;

  // Group verified citations by their actual document ID.
  const citationGroups =
    answer?.citations.reduce<Record<string, Citation[]>>(
      (groups, citation) => {
        const key = citation.document_id || citation.filename;
        (groups[key] ??= []).push(citation);
        return groups;
      },
      {}
    ) ?? {};

  return (
    <div className="content-width">
      <section className="page-intro">
        <div className="eyebrow"><span className="eyebrow-line"/> HOSPITALITY DESIGN INTELLIGENCE</div>
        <h1>Every project detail,<br/><em>within reach.</em></h1>
        <p>Search across project specifications, approved finishes, supplier quotations and renovation history — with evidence you can trace.</p>
      </section>

      <section className="search-card">
        <div className="mode-tabs" role="tablist" aria-label="Search mode">
          <button role="tab" aria-selected={mode === "ask"} className={mode === "ask" ? "mode-tab selected" : "mode-tab"} onClick={() => setMode("ask")}><WandSparkles size={16}/> Ask AI</button>
          <button role="tab" aria-selected={mode === "search"} className={mode === "search" ? "mode-tab selected" : "mode-tab"} onClick={() => setMode("search")}><Search size={16}/> Explore evidence</button>
        </div>
        <form onSubmit={run}>
          <label className="input-label" htmlFor="question-input">YOUR QUESTION</label>
          <div className="question-control">
            <textarea id="question-input" value={question} maxLength={500} rows={3}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What would you like to know about your hospitality projects?"/>
          </div>
          <div className="search-actions">
            <label className="project-field">Project ID <input aria-label="Optional project ID filter" value={project} maxLength={80} onChange={(e) => setProject(e.target.value)} placeholder="All projects"/></label>
            <button className="primary-button" type="submit" disabled={loading || question.trim().length < 5}>
              {loading ? <><LoaderCircle size={17} className="spin"/> Working...</> : <>{mode === "ask" ? "Generate answer" : "Find evidence"}<ArrowUpRight size={17}/></>}
            </button>
          </div>
        </form>
      </section>

      {!hasResponse && !loading && <section className="suggestions">
        <div className="section-overline">TRY AN EXAMPLE</div>
        <div className="suggestion-grid">
          {examples.map((example, i) => <button key={example} className="suggestion" onClick={() => { setQuestion(example); setProject(""); }}>
            <span className="suggestion-icon">{i === 0 ? <ShieldCheck size={18}/> : i === 1 ? <FileText size={18}/> : <Layers3 size={18}/>}</span>
            <span>{example}</span><ChevronRight size={15} className="suggestion-arrow"/>
          </button>)}
        </div>
      </section>}

      {error && <div className="feedback-error" role="alert">{error}</div>}
      {loading && <div className="loading-panel"><LoaderCircle size={22} className="spin"/><span>{mode === "ask" ? "Retrieving approved project records and checking citations…" : "Running keyword, vector and reranking retrieval…"}</span></div>}

      {answer && <section className="results-area" aria-live="polite">
        <div className="results-heading"><span className="section-overline">KNOWLEDGE RESPONSE</span><span className={`result-status ${answer.status === "answered" ? "status-positive" : "status-neutral"}`}>{answer.status === "answered" ? "Evidence available" : "Insufficient evidence"}</span></div>
        <article className="answer-panel">
          <div className="answer-panel-title"><div className="answer-spark"><Sparkles size={18}/></div><div><strong>Grounded answer</strong><span>Generated from accessible records</span></div></div>
          <p className="answer-content">{answer.answer}</p>
          <div className="answer-meta"><span><ShieldCheck size={15}/> Citation integrity: {answer.citation_integrity.replaceAll("_", " ")}</span>{answer.usage?.model && <span><MessageSquareText size={15}/>{answer.usage.model}</span>}</div>
          {answer.status === "insufficient_evidence" && <div className="abstain-notice">No verified answer was returned. Check document availability, access permissions, and whether the records contain the requested details. Reason: {answer.reason?.replaceAll("_", " ") || "evidence unavailable"}.</div>}
        </article>

          {answer.citations.length > 0 && (
            <>
              <div className="section-title-row">
                <h2>
                  Source documents{" "}
                  <span>{Object.keys(citationGroups).length}</span>
                </h2>
                <span className="soft-caption">
                  {answer.citations.length} verified supporting excerpts
                </span>
              </div>

              <div className="citation-document-list">
                {Object.entries(citationGroups).map(
                  ([documentId, citations], index) => {
                    const document = citations[0];

                    return (
                      <article
                        className="citation-card citation-document-card"
                        key={documentId}
                      >
                        <div className="citation-card-top">
                          <span className="citation-number">
                            {String(index + 1).padStart(2, "0")}
                          </span>

                          <span className="verified-tag">
                            <ShieldCheck size={13} />
                            Verified source
                          </span>
                        </div>

                        <div className="citation-filename">
                          <FileText size={18} />
                          <strong>{document.filename}</strong>
                        </div>

                        <div className="citation-location">
                          {document.project_code
                            ? `Project ${document.project_code} · `
                            : ""}
                          {citations.length} verified{" "}
                          {citations.length === 1 ? "excerpt" : "excerpts"}
                        </div>

                        <details className="citation-excerpts">
                          <summary>
                            <span>
                              View {citations.length} supporting{" "}
                              {citations.length === 1
                                ? "excerpt"
                                : "excerpts"}
                            </span>
                            <ChevronRight size={17} />
                          </summary>

                          <div className="citation-excerpt-list">
                            {citations.map((citation, quoteIndex) => (
                              <div
                                className="citation-excerpt"
                                key={`${citation.chunk_id}-${quoteIndex}`}
                              >
                                <div className="citation-excerpt-label">
                                  EVIDENCE{" "}
                                  {String(quoteIndex + 1).padStart(2, "0")}
                                </div>

                                <div className="citation-excerpt-location">
                                  {humanSource(citation.source)}
                                </div>

                                <blockquote>
                                  “{citation.supporting_quote}”
                                </blockquote>
                              </div>
                            ))}
                          </div>
                        </details>
                      </article>
                    );
                  }
                )}
              </div>
            </>
          )}

      </section>}

      {search && <section className="results-area" aria-live="polite">
        <div className="section-title-row"><h2>Retrieved evidence <span>{search.results.length}</span></h2><span className="soft-caption">Authorized source chunks only</span></div>
        {search.results.length === 0 ? <div className="empty-results">No matching records were found for this demo identity and query.</div> :
          <div className="evidence-list">{search.results.map((item, index) => <article className="evidence-card" key={item.chunk_id}>
            <div className="evidence-header"><span className="evidence-rank">MATCH {String(index + 1).padStart(2, "0")}</span><span className="evidence-filename"><FileText size={16}/>{item.filename}</span></div>
            <div className="evidence-location">{humanSource(item.source)}{item.project_code ? ` · ${item.project_code}` : ""}</div>
            <p>{item.text}</p>
            <div className="evidence-footer">RRF {item.rrf_score.toFixed(4)} <span>·</span> Reranker {item.rerank_score.toFixed(3)} <span>·</span> Scores are not confidence probabilities</div>
          </article>)}</div>}
      </section>}

      {retrieval && <div className="metrics-strip" aria-label="Retrieval diagnostics">
        <span><FileSearch size={16}/> Keyword candidates <strong>{retrieval.keyword_candidates ?? "—"}</strong></span>
        <span><Layers3 size={16}/> Vector candidates <strong>{retrieval.vector_candidates ?? "—"}</strong></span>
        <span><Clock3 size={16}/> Retrieval <strong>{retrieval.latency_ms ?? "—"} ms</strong></span>
      </div>}

      <div className="search-note"><BookOpenText size={18}/><span>Missing project knowledge? <button onClick={onOpenLibrary}>Go to Document Library</button> to upload synthetic sample records using the administrator identity.</span></div>
    </div>
  );
}
