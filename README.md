# OpenMontage

Servizio web (Streamlit) per la produzione video locale con **Ollama** + **FFmpeg** +
**HyperFrames**, containerizzato con Docker.

## Configurazione (`.env`)

Il servizio legge le credenziali dal file `.env` (gestito da ai4educ Console):

| Variabile | Uso |
|-----------|-----|
| `ANALISI_PDF_OLLAMA_HOST` | Endpoint HTTP del server Ollama (es. `http://192.168.129.14:11434`) |
| `DEEPSEEK_SBS_API_DEEPSEEK` | API key DeepSeek (opzionale) |

La selezione del modello avviene interrogando `GET {OLLAMA_HOST}/api/tags`
(preferendo una variante `gemma`).

## Avvio con Docker

```bash
docker compose up --build
```

Apri poi `http://localhost:8502` (porta host mappata su `8501` nel container).

> L'engine `openmontage_engine/` **non è versionato**: il Dockerfile lo clona
> al build da `RayCodes_OpenMontage` (override con build arg `ENGINE_REPO`/`ENGINE_REF`).

## Rendering video

La pipeline HyperFrames richiede un clip di riferimento `reference_video.mp4`.
Crea la cartella `media/`, inserisci un breve `.mp4` e abilita il mount in
`docker-compose.yml`:

```yaml
    volumes:
      - ./media/reference_video.mp4:/app/reference_video.mp4:ro
```

Gli output finiscono in `sample_output/` e i workspace in `projects/`
(entrambi montati come volumi).

## Struttura

```
├── app.py                # Dashboard Streamlit (servizio web)
├── pipeline.py           # Orchestrazione: Ollama (HTTP) + HyperFrames render
├── requirements.txt
├── Dockerfile            # Python 3.11 + Node 22 + FFmpeg + Chrome Headless Shell
├── docker-compose.yml
└── README.md
# openmontage_engine/  -> clonato al build, NON versionato
# sample_output/, projects/, media/, *.mp4 -> generati/runtime, ignorati da git
```

## Sviluppo locale (senza Docker)

Richiede Python 3.10+, Node ≥ 22, FFmpeg.

```bash
pip install -r requirements.txt
# l'engine non è nel repo: clonalo accanto ai sorgenti
git clone --depth 1 https://github.com/47thtechcorner/RayCodes_OpenMontage /tmp/om \
  && cp -a /tmp/om/openmontage_engine . && rm -rf /tmp/om
npx hyperframes browser ensure
streamlit run app.py
```
