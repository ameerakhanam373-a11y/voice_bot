# Full Stack Academy Customer Agent

**A student support demo with a distinct Customer Desk interface.** It combines local document search and mock support tools with Groq-hosted or local LLM chat, Streamlit, optional speech, and an isolated LiveKit worker entry point.

> **Demo data:** Full Stack Academy is fictional in this repository. The included PDFs and student record are examples created for this project. Replace them with approved material before using this software with real customers. Do not enter real personal, account, or payment details.

##What I built
Built a voice bot that takes spoken input, processes the request, and responds with synthesized speech. The project connects speech recognition   and text-to-speech into a conversational voice interface.
 
## What it does

- Answers questions from local Academy PDFs using retrieval augmented generation (RAG).
- Shows the source filename, page, matched text, and similarity score below an answer.
- Offers a mock student status lookup and simulated human escalation.
- Runs chat through Streamlit or a terminal.
- Supports local speech to text with Faster Whisper and offline speech synthesis with pyttsx3; Piper is optional.
- Includes an optional LiveKit worker for room based voice transport.

## Architecture

~~~text
                         ┌── local PDF files
                         │         │
Browser ── Streamlit ── Local Whisper (voice upload)
    │                    │         │
    └──── chat text ── Groq API or local LLM (LM Studio / Ollama)
                              │
                         LangChain tools
                       ┌──────┴──────┐
                 Local Qdrant    Mock account
                       │
              Local sentence embeddings

Final response ── Local system voice (pyttsx3) ── Browser audio player

Optional room deployment: LiveKit Agents worker + a LiveKit server
~~~

## Local/free demo

Choose either Groq's hosted API or a local model server. With Groq, user questions and retrieved document snippets are sent to Groq for generation; the PDF index and embeddings remain on this computer. Groq offers a free tier with rate limits, and its paid Developer tier requires a payment method. With LM Studio or Ollama, model requests remain local. The first embedding and Whisper model use downloads from their open-source model repositories; those downloads may be several hundred megabytes.

### Requirements

- Python 3.11 or newer
- A Groq API key, or LM Studio/Ollama with an OpenAI-compatible API enabled
- About 2 GB of RAM for all-MiniLM-L6-v2 embeddings, in addition to the language model's needs
- Optional voice: Faster Whisper model files; pyttsx3 uses installed system voices

### Windows PowerShell setup

~~~powershell
git clone https://github.com/YOUR-USERNAME/full-stack-academy-customer-agent.git
cd full-stack-academy-customer-agent
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
~~~

Use Python 3.11 or newer. These commands call the virtual environment's Python directly, so PowerShell script activation settings do not get in the way. In VS Code, the workspace is set to use .venv automatically after it is created.

### Configure Groq or a local model

Groq is the default configuration:

1. Create an API key in the [Groq Console](https://console.groq.com/keys).
2. Open .env and replace your-groq-api-key with the key. Keep it private; never commit .env or paste the key into chat.
3. The default model is openai/gpt-oss-20b, which supports tool calling. Groq's OpenAI-compatible API uses https://api.groq.com/openai/v1.

The Groq free plan has request and token limits; limits can change. A paid Developer tier is optional and requires a payment method. Check the [current rate limits](https://console.groq.com/docs/rate-limits) and [billing details](https://console.groq.com/docs/billing-faqs). Requests and retrieved snippets are sent to Groq, so use only the fictional sample data unless you have reviewed the provider's data handling terms.

To use a local model instead, set LLM_BASE_URL=http://localhost:1234/v1, LLM_API_KEY=lm-studio, and LLM_MODEL to the exact ID shown in LM Studio. For Ollama, set LLM_BASE_URL=http://localhost:11434/v1 and set LLM_API_KEY=ollama plus the pulled model name.

### Index the included documents

~~~powershell
.\.venv\Scripts\python.exe ingest.py
~~~

This creates qdrant_db/ locally. The index is excluded from Git and can be rebuilt at any time. Add or replace PDFs under docs/ and run ingestion again. Reingestion replaces the collection, so old chunks do not accumulate. Four fictional PDFs are included to make a fresh clone ready to index.

### Start the app

~~~powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
~~~

The sidebar checks the model endpoint, Qdrant index, PDF directory, and local TTS package. Chat needs a valid Groq key or a running local model, plus an indexed knowledge base for Academy policy questions.

Run the terminal client with:

~~~powershell
.\.venv\Scripts\python.exe main.py console
~~~

python main.py starts the same console mode. Type quit to exit.

## Local voice setup

The Streamlit audio uploader transcribes speech on the computer with Faster Whisper. WHISPER_MODEL accepts tiny, base, small, and medium. Larger models usually improve accuracy and use more memory and time. As a rough CPU guide, plan for about 1 GB RAM for tiny, 1–2 GB for base, 2–3 GB for small, and 5+ GB for medium; actual use depends on quantization, audio length, and platform. base is the default balance for a classroom demo.

On Windows, the default TTS uses pyttsx3 and your installed offline system voices. It needs no separate voice model download. Set TTS_VOICE to default in .env, or set it to an installed system voice ID to choose a voice. This package calls the operating system's local speech engine and works offline.

Piper is available as an optional backend. Its pinned phonemizer dependency does not provide compatible packages for every Python version on Windows, so it is kept out of the standard install. To use it, install Python 3.11, create the virtual environment with that interpreter, install requirements.txt and requirements-voice-piper.txt, download the en_US-lessac-medium model and matching .onnx.json file from the [Piper voices project](https://github.com/rhasspy/piper/blob/master/VOICES.md), place them in models/, then set TTS_ENGINE=piper and TTS_VOICE=./models/en_US-lessac-medium.onnx in .env. The JSON config must have the same basename.

If voice packages or model files are unavailable, text chat remains usable. Whisper model weights download the first time the model is loaded.

## LiveKit real-time deployment

LiveKit room transport is an optional deployment path, separate from the local Streamlit demo. It requires a LiveKit server (self-hosted or a developer account) and a microphone-capable client connected to a room. A hosted service may have quotas or paid usage; check its current plan before deployment. LiveKit itself is open source and can be self-hosted.

The included worker entry point is python main.py dev. It uses the LiveKit Agents SDK, the local OpenAI-compatible LLM, and compatible STT and TTS endpoints. Set LIVEKIT_STT_BASE_URL and LIVEKIT_TTS_BASE_URL to local services that expose OpenAI-compatible APIs, plus LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET for your room server. An STT endpoint such as a local Faster Whisper server and a TTS endpoint such as a local Kokoro server can keep model processing local. The worker includes the same RAG, mock account, and escalation tools. The standalone Streamlit audio upload path is the simpler fully local speech option and needs no LiveKit room.

For a hosted room service, create a separate development project and follow its current connection instructions. For a self-hosted room server, point the worker/client to that server. Do not commit room credentials. The local text and upload demo does not need a LiveKit account or credit card.

## Tools and boundaries

| Tool | Purpose |
| --- | --- |
| search_academy_information | Searches local PDF chunks for documented answers. |
| check_student_account | Reads one fictional mock record (FSA1001) from tools.py. |
| request_human_support | Returns a simulated escalation confirmation. It does not send a message. |

The assistant is instructed to avoid inventing facts and to escalate real account access, complaints, exceptions, and requests that need a staff decision. The mock account tool is not connected to a real system.

##Project summary
This project explores how voice interfaces can make it easier to interact with an AI assistant. It combines speech input, response generation, and spoken output in one application.

## Repository map

~~~text
agent.py               Local LLM orchestration and tool-call loop
config.py              Environment-based settings
create_sample_docs.py  Regenerates the fictional starter PDFs
docs/                  Four source PDFs for the demo
ingest.py              PDF loading, splitting, embeddings, and local indexing
livekit_voice.py       Optional room worker
main.py                Terminal client and worker entry point
rag.py                 Local Qdrant search and source metadata
streamlit_app.py       Customer Desk web interface
tools.py               Academy search, mock account, and escalation tools
voice.py               Local Faster Whisper and Piper helpers
~~~

## Troubleshooting

- **Model endpoint unavailable:** for Groq, check the API key and endpoint; for a local model, start LM Studio/Ollama and check LLM_BASE_URL.
- **Groq authentication error:** replace the placeholder LLM_API_KEY in .env with your key, save the file, then restart Streamlit.
- **Groq rate-limit or quota error:** wait for the free-tier limits to reset or review the provider's current limits.
- **Tool calls or malformed replies:** choose an instruct/chat model with function calling enabled and set the exact model name in .env.
- **No indexed documents:** add PDFs to docs/ and run python ingest.py. The first embedding download needs internet access.
- **Embedding install or memory issues:** sentence-transformers and PyTorch are large packages. Use a 64-bit Python 3.11 environment and allow the first model download to finish.
- **Whisper is slow:** choose tiny or base, use shorter audio, or use a machine with a supported GPU. CPU mode is selected by default.
- **Piper cannot find a voice:** confirm the .onnx model path and matching .onnx.json file under models/.
- **Port already in use:** configure a different Streamlit port with streamlit run streamlit_app.py --server.port 8502.
- **Qdrant local database locked:** stop other app or ingestion processes using qdrant_db/, then rerun ingestion.

## GitHub upload checklist

1. Review and replace the fictional PDFs if you want your own Academy content.
2. Keep .env, qdrant_db/, and voice model files out of Git (the included .gitignore does this).
3. Create and push the repository:

~~~powershell
git init
git add .
git commit -m "Build local-first Academy customer agent"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/full-stack-academy-customer-agent.git
git push -u origin main
~~~

## License

Choose a license before publishing if you want others to reuse the code. Check the licenses of model weights or documents you add separately.
