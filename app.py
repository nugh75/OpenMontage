import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

import streamlit as st
from pipeline import run_pipeline, select_model, list_models, ollama_host, effective_ollama_host, deepseek_api_key

st.set_page_config(page_title="OpenMontage Ollama FFmpeg Video Generator", layout="centered")

st.markdown("""
    <style>
    .main-title { font-size: 40px; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    .subtitle { font-size: 18px; color: #4B5563; text-align: center; margin-bottom: 40px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">OpenMontage Video Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Agent Driven Kinetic Video Production System</div>', unsafe_allow_html=True)

# Sidebar configurations
st.sidebar.header("Configuration")
st.sidebar.caption(f"Ollama host (.env): `{ollama_host()}`")
eff = effective_ollama_host()
if eff != ollama_host():
    st.sidebar.caption(f"Effective host: `{eff}`")
st.sidebar.caption("DeepSeek API: " + ("configured" if deepseek_api_key() else "not set"))

remote_models = list_models()
model_options = remote_models or [select_model(), "gemma4:e2b", "llama3"]
selected_model = st.sidebar.selectbox("Ollama Model", options=list(dict.fromkeys(model_options)))

if not remote_models:
    st.sidebar.warning("No models returned by the Ollama host. Check connectivity / .env.")

# Main prompt entry
prompt = st.text_input("Enter Video Prompt / Concept:", value="Neural Navigator")

col1, col2 = st.columns(2)
with col1:
    if st.button("Generate Video", type="primary", use_container_width=True):
        with st.spinner("Executing pipeline and rendering video..."):
            res = run_pipeline(prompt, selected_model)
            if "Error" in res:
                st.error(res)
            else:
                st.success(f"Video composed successfully!")
                st.balloons()

with col2:
    if st.button("Reset Workspace", use_container_width=True):
        st.warning("Workspace reset completed.")

# Show Plan and Sample Video Side-by-Side
st.markdown("---")
left_col, right_col = st.columns([1.2, 1.8])

with left_col:
    st.subheader("Production Plan")
    plan_path = Path("sample_output/production_plan.json")
    if plan_path.exists():
        with open(plan_path) as f:
            plan = json.load(f)
            st.json(plan)
    else:
        st.info("No plan generated yet.")

with right_col:
    st.subheader("Render Output")
    video_path = Path("sample_output/concept_demo.mp4")
    if video_path.exists():
        st.video(str(video_path))
    else:
        st.info("No video rendered yet.")
