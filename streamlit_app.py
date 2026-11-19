"""Distinctive Streamlit demo for the Full Stack Academy customer agent."""
import tempfile
from pathlib import Path
import requests
import streamlit as st

from agent import AgentError, answer_question
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, DOCS_DIR
from rag import knowledge_base_status
from voice import transcribe_audio, synthesize_speech, voice_status

st.set_page_config(page_title="Full Stack Academy · Customer Desk", page_icon="◈", layout="wide")
st.markdown("""
<style>
:root{--ink:#f1f2f7;--muted:#9da2b6;--base:#10111b;--panel:#191b29;--line:#2a2d3d;--lime:#c7f36b;--pink:#ff7f8b}
.stApp{background:radial-gradient(ellipse at 70% -10%,#292b4266,transparent 42%),var(--base);color:var(--ink);font-family:Inter,'Segoe UI',sans-serif}
[data-testid="stSidebar"]{background:#151622;border-right:1px solid var(--line)}
h1,h2,h3,p,span,label{font-family:'Manrope',sans-serif}
.brand{display:flex;align-items:center;gap:14px;margin:4px 0 28px}.brand-mark{display:grid;place-items:center;width:48px;height:48px;background:var(--lime);color:#131519;border-radius:14px;font-size:25px;font-weight:800}
.eyebrow{font:500 11px ui-monospace,monospace;color:var(--lime);letter-spacing:.14em;text-transform:uppercase}
.hero-title{font-size:clamp(32px,4vw,48px);line-height:1.08;letter-spacing:-.05em;font-weight:800;margin:10px 0}.hero-copy{color:var(--muted);max-width:650px;font-size:15px;line-height:1.7}
.status-pill{font:11px ui-monospace,monospace;border:1px solid var(--line);padding:7px 10px;border-radius:99px;color:var(--muted);display:inline-block;margin:5px 5px 3px 0}.status-ok{color:var(--lime);border-color:#536534}.status-bad{color:var(--pink);border-color:#70404a}
.stChatMessage{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 18px}[data-testid="stChatInput"]{border-color:#464a60!important}
.stButton>button{border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--ink)}div[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px}.tiny{font:11px ui-monospace,monospace;color:var(--muted)}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">◈</div><div><div style="font-weight:800">FULL STACK</div><div class="eyebrow">ACADEMY / SUPPORT</div></div></div>', unsafe_allow_html=True)
    st.markdown("### Local setup")
    st.caption(f"Model · `{LLM_MODEL}`")
    if "api.groq.com" in LLM_BASE_URL:
        provider_name = "Groq API"
    elif "11434" in LLM_BASE_URL:
        provider_name = "Ollama local"
    elif "localhost" in LLM_BASE_URL or "127.0.0.1" in LLM_BASE_URL:
        provider_name = "LM Studio / local"
    else:
        provider_name = "OpenAI-compatible API"
    st.caption(f"Provider · {provider_name}")
    st.caption("Retrieval · Qdrant Local + MiniLM")
    q_ok, _ = knowledge_base_status()
    v_ok, _ = voice_status()
    try:
        llm_ok = requests.get(
            f"{LLM_BASE_URL}/models",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {},
            timeout=4,
        ).ok
    except requests.RequestException:
        llm_ok = False
    docs_ok = any(DOCS_DIR.glob("*.pdf"))
    st.markdown("### System pulse")
    for label, ok in [("LLM server", llm_ok), ("Qdrant index", q_ok), ("Academy PDFs", docs_ok), ("Local TTS", v_ok)]:
        st.markdown(f'<span class="status-pill {"status-ok" if ok else "status-bad"}">{"●" if ok else "○"} {label}</span>', unsafe_allow_html=True)
    if "api.groq.com" in LLM_BASE_URL:
        st.caption("Groq handles model requests online. Free tier limits apply; retrieved data is sent with each question.")
    else:
        st.caption("Local model requests stay on this computer. LiveKit room transport is optional.")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_meta = {}
        st.rerun()

st.markdown('<div class="eyebrow">STUDENT HELP · ALWAYS LEARNING</div><div class="hero-title">Your next step,<br>made clearer.</div><div class="hero-copy">Ask about programs, admissions, tuition, or student support. Answers come from the local Academy guide, with sources shown beneath each reply.</div>', unsafe_allow_html=True)
st.markdown('<span class="status-pill">LOCAL FIRST</span><span class="status-pill">SOURCE GROUNDED</span><span class="status-pill">DEMO KNOWLEDGE BASE</span>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_meta" not in st.session_state:
    st.session_state.last_meta = {}


def show_meta(meta):
    if meta.get("sources"):
        with st.expander(f"Retrieved sources · {len(meta['sources'])} chunks"):
            for source in meta["sources"]:
                st.markdown(f"**{source['source']}** · page {source['page']} · similarity {source['score']:.2f}")
                st.caption(source["text"])
    if meta.get("tools"):
        with st.expander("Tools used"):
            for item in meta["tools"]:
                st.caption(f"{item['name']} · {item['status']}")


for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            show_meta(st.session_state.last_meta.get(str(idx), {}))


def reply(question: str):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("assistant"):
        with st.spinner("Checking the Academy guide…"):
            try:
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                result = answer_question(question, history)
                answer = result["answer"]
                st.markdown(answer)
            except AgentError as exc:
                result = {"answer": f"I can’t reach the local AI model right now. {exc}", "sources": [], "tools": []}
                answer = result["answer"]
                st.error(answer)
            except Exception:
                result = {"answer": "I couldn’t complete that request. Please check that the knowledge base is indexed and try again.", "sources": [], "tools": []}
                answer = result["answer"]
                st.error(answer)
        new_index = len(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_meta[str(new_index)] = result
        show_meta(result)


prompt = st.chat_input("Ask the Academy…")
if prompt:
    reply(prompt)

with st.expander("Try a sample question"):
    examples = ["Which program is designed for beginners?", "What are the demo admission steps?", "I can’t access the learning portal. What should I try?"]
    cols = st.columns(len(examples))
    for col, example in zip(cols, examples):
        if col.button(example, use_container_width=True):
            reply(example)

st.divider()
st.markdown("#### Voice desk <span class='tiny'>· local transcription and playback</span>", unsafe_allow_html=True)
audio = st.file_uploader("Upload a voice question", type=["wav", "mp3", "m4a", "webm"], label_visibility="collapsed")
if audio and st.button("Transcribe and ask", type="primary"):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.name).suffix or ".wav") as temp:
            temp.write(audio.getvalue())
            audio_path = temp.name
        with st.spinner("Listening locally with Whisper…"):
            transcript = transcribe_audio(audio_path)
        if transcript:
            st.info(f"You said: {transcript}")
            reply(transcript)
            try:
                st.audio(synthesize_speech(st.session_state.messages[-1]["content"]))
            except Exception as exc:
                st.caption(f"Speech playback unavailable: {exc}")
        else:
            st.warning("No speech was detected. Try a clearer recording.")
    except Exception as exc:
        st.error(f"Voice processing is unavailable: {exc}")
