# CONTEXT — OpenMontage

<!-- ai4educ:context-template v1.0 -->

## Quick Reference
- **Stack**: Python, Streamlit, Node.js (HyperFrames), Ollama, FFmpeg, Docker
- **Entry point**: `docker compose up --build` o `streamlit run app.py` (porta 8502)
- **Test**: `make test-contracts` (in openmontage_engine/)

## Domain
Servizio web per produzione video locale che combina AI generativa (Ollama) con rendering HyperFrames e FFmpeg. Interfaccia Streamlit. Il motore di rendering è in `openmontage_engine/` (progetto separato).

### Key Directories
- `app.py` — interfaccia Streamlit
- `openmontage_engine/` — motore di pipeline video (progetto indipendente)
- `pipeline_defs/` — definizioni pipeline
