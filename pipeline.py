import os
import sys
import subprocess
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

# Bring openmontage_engine into import path
sys.path.insert(0, str(Path(__file__).resolve().parent / "openmontage_engine"))
from tools.video.hyperframes_compose import HyperFramesCompose


def _clean(value: str) -> str:
    """Strip whitespace and surrounding quotes.

    Docker `env_file` / `--env-file` inject values verbatim (quotes kept),
    unlike python-dotenv which strips them. Normalize either way.
    """
    value = (value or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def ollama_host() -> str:
    """Resolve the configured Ollama HTTP endpoint from the environment (.env)."""
    host = _clean(
        os.environ.get("ANALISI_PDF_OLLAMA_HOST")
        or os.environ.get("OLLAMA_HOST")
        or "http://localhost:11434"
    )
    return host.rstrip("/")


def _ollama_candidates() -> list[str]:
    """Endpoints to try, in order: configured host, then a host-gateway
    fallback (same port) for Docker Desktop / WSL2 where the LAN IP in the
    .env is only routable from the host, not from inside the container.
    """
    primary = ollama_host()
    cands = [primary]
    try:
        from urllib.parse import urlparse

        port = urlparse(primary).port or 11434
    except Exception:
        port = 11434
    fallback_env = _clean(os.environ.get("OLLAMA_FALLBACK_HOST") or "")
    for extra in (fallback_env, f"http://host.docker.internal:{port}"):
        extra = extra.rstrip("/")
        if extra and extra not in cands:
            cands.append(extra)
    return cands


_RESOLVED_BASE: str = ""


def effective_ollama_host() -> str:
    """Return the first reachable Ollama base URL (cached for the process)."""
    global _RESOLVED_BASE
    if _RESOLVED_BASE:
        return _RESOLVED_BASE
    candidates = _ollama_candidates()
    try:
        import requests

        for base in candidates:
            try:
                r = requests.get(f"{base}/api/tags", timeout=4)
                if r.ok:
                    _RESOLVED_BASE = base
                    return base
            except Exception:
                continue
    except Exception:
        pass
    _RESOLVED_BASE = candidates[0]
    return _RESOLVED_BASE


def deepseek_api_key() -> str:
    """Optional DeepSeek API key sourced from the environment (.env)."""
    return _clean(
        os.environ.get("DEEPSEEK_SBS_API_DEEPSEEK")
        or os.environ.get("DEEPSEEK_API_KEY")
        or ""
    )


def list_models() -> list[str]:
    """List models exposed by the remote Ollama host (HTTP /api/tags).

    Falls back to the local `ollama` CLI, then to an empty list.
    """
    base = effective_ollama_host()
    try:
        import requests

        res = requests.get(f"{base}/api/tags", timeout=5)
        res.raise_for_status()
        models = [m.get("name", "") for m in res.json().get("models", [])]
        return [m for m in models if m]
    except Exception:
        pass
    try:
        res = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
        return [line.split()[0] for line in res.stdout.splitlines()[1:] if line.strip()]
    except Exception:
        return []


def select_model() -> str:
    """Pick the best available model, preferring a Gemma 4 variant."""
    models = list_models()
    for m in models:
        if "gemma" in m.lower():
            return m
    if models:
        return models[0]
    return "gemma4:e2b"


def run_pipeline(prompt: str, model_name: str = None) -> str:
    """Run the OpenMontage HyperFrames rendering pipeline."""
    model = model_name or select_model()
    print(f"Ollama host: {ollama_host()} (effective: {effective_ollama_host()})")
    print(f"Using Ollama Model: {model}")

    reference = Path("reference_video.mp4")
    if not reference.exists():
        return (
            "Error: reference_video.mp4 not found. Mount or place a short .mp4 "
            "named 'reference_video.mp4' in the working directory."
        )

    workspace = Path("projects/neural-navigator/hyperframes")
    out_video = Path("sample_output/concept_demo.mp4")
    out_video.parent.mkdir(parents=True, exist_ok=True)

    composer = HyperFramesCompose()
    composer.execute({
        "operation": "scaffold_workspace",
        "workspace_path": str(workspace),
        "asset_manifest": {"version": "1.0", "assets": [{"id": "bg", "type": "video", "path": str(reference.resolve()), "source_tool": "local", "scene_id": "sc1"}]},
        "edit_decisions": {"version": "1.0", "cuts": [{"id": "cut_bg", "source": "bg", "in_seconds": 0.0, "out_seconds": 5.0}]},
    })

    # Copy the pre-built cinematic HTML template to the workspace
    template_path = Path(__file__).resolve().parent / "openmontage_engine" / "templates" / "cinematic_template.html"
    if template_path.exists():
        (workspace / "index.html").write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")

    print("Rendering final composition with Chrome Headless Shell...")
    cmd = ["npx", "--yes", "hyperframes", "render", "--output", str(out_video.resolve()), "--fps", "30", "--quality", "standard"]
    if sys.platform == "win32":
        resolved_npx = shutil.which("npx")
        if resolved_npx:
            cmd[0] = resolved_npx
    try:
        subprocess.run(cmd, cwd=str(workspace), check=True, capture_output=True, text=True)
        print(f"Success! Video rendered to: {out_video}")
        return str(out_video)
    except subprocess.CalledProcessError as e:
        return f"Error during rendering: {e.stderr}"


if __name__ == "__main__":
    print(run_pipeline("Neural Navigator"))
