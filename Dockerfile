FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_MAJOR=22 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    HOME=/root

# System dependencies: git + ffmpeg + Chrome Headless Shell runtime libs + Node toolchain prereqs
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg git ffmpeg \
        fonts-liberation libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
        libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
        libx11-6 libxcb1 libxext6 libxi6 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 (required by HyperFrames composition engine)
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# The OpenMontage engine is NOT vendored in this repo: it is fetched at build
# time so the repository stays minimal. Override the source with build args.
ARG ENGINE_REPO=https://github.com/47thtechcorner/RayCodes_OpenMontage
ARG ENGINE_REF=main
RUN git clone --depth 1 --branch "$ENGINE_REF" "$ENGINE_REPO" /tmp/upstream \
    && cp -a /tmp/upstream/openmontage_engine ./openmontage_engine \
    && mkdir -p ./sample_output \
    && (cp -a /tmp/upstream/sample_output/production_plan.json ./sample_output/ || true) \
    && rm -rf /tmp/upstream

# Application code (the only sources versioned in git)
COPY app.py pipeline.py ./

# Pre-fetch the HyperFrames CLI + Chrome Headless Shell (non-fatal at build time)
RUN npx --yes hyperframes browser ensure || echo "warning: hyperframes browser ensure skipped (will retry at runtime)"

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
