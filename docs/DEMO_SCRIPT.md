# 3–5 minute demo — Asteria Studio (record from the local UI)

**0:00–0:30 | Business need**
'Hotel interior-design consultancies receive material approvals, fire-document registers, supplier quotes and project briefs in disconnected formats. Asteria Studio helps staff locate authorized project information and inspect evidence.' Show the fictional synthetic dataset disclaimer.

**0:30–1:15 | Upload and ingestion**
Switch to the **Asteria demo administrator** (the current demo uploads are admin-only, not ordinary designer uploads). Upload a safe synthetic DOCX or PDF. Show queued → processing → ready, then explain Docling/parser, chunks, local embeddings, pgvector, and optional S3 storage. **Do not claim S3 live unless its smoke test passed.**

**1:15–2:10 | Knowledge discovery**
Switch to `aster-designer`. Search for Solstice Grand Resort upholstery approval and fire-document submission. Show ranked results and source references. Ask a previously validated question. If Groq returns insufficient evidence, explain safe abstention; do not edit the footage to imply a verified answer appeared.

**2:10–2:55 | Citations / human audit**
Show supporting excerpt, filename and source location. Explain that exact quote matching verifies provenance only; a human still has to confirm whether claims are supported. If the UI lacks a clickable full document preview, show the available citation metadata instead—do not imply a feature that does not exist.

**2:55–3:40 | Permissions / tenant isolation**
As `aster-procurement`, show restricted supplier quotation access. Switch to `aster-designer` to demonstrate absence of procurement-only price files, then `rival-designer` to show no Asteria documents. State demo-header auth is not real SSO.

**3:40–4:30 | Engineering / evidence**
Present the `docs/ARCHITECTURE.md` diagram, API/worker separation, PostgreSQL/pgvector, hybrid RRF/reranking, test suite and `docs/EVALUATION.md`. State pilot Recall@5 1.0 on only 3 docs; hybrid MRR@5 0.833 vs keyword 0.889, original answer check 10/15.

**4:30–5:00 | Close**
'Synthetic, reproducible case study focused on permission-aware document intelligence. Remaining work: larger ground-truth corpus, stronger citations, production authentication, and AWS deployment.'

Record the real UI, not only console commands. Use only confirmed outputs; don't claim real customers, completed cloud deployment, independent fire certification or perfect answer accuracy.
