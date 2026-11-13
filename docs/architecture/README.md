# Asteria Studio — Architecture figures

The diagrams in this directory accompany the root README:

- `implemented-system.svg` / `.png` — implemented application, data ingestion, permissions, and hybrid RAG services.
- `rag-workflow.svg` / `.png` — specialized upload-to-answer pipeline.
- `aws-production-reference.svg` / `.png` — enterprise production reference architecture with AWS services.
- `render_architecture.py` — editable vector-diagram source; regenerates all figures.

SVGs are editable in most vector design tools. To regenerate the PNG and SVG outputs, install `svgwrite` and `cairosvg` in an isolated environment, then run `python render_architecture.py` from this directory.
