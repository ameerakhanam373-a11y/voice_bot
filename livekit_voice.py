"""Optional LiveKit room worker using OpenAI-compatible local model endpoints."""
import os

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from tools import check_student_account, request_human_support, search_academy_information


def run_worker() -> None:
    stt_url = os.getenv("LIVEKIT_STT_BASE_URL", "").strip()
    tts_url = os.getenv("LIVEKIT_TTS_BASE_URL", "").strip()
    missing = [name for name, value in [
        ("LIVEKIT_URL", os.getenv("LIVEKIT_URL")),
        ("LIVEKIT_API_KEY", os.getenv("LIVEKIT_API_KEY")),
        ("LIVEKIT_API_SECRET", os.getenv("LIVEKIT_API_SECRET")),
        ("LIVEKIT_STT_BASE_URL", stt_url),
        ("LIVEKIT_TTS_BASE_URL", tts_url),
    ] if not value]
    if missing:
        raise SystemExit(
            "LiveKit room mode needs a LiveKit server and OpenAI-compatible STT/TTS endpoints. "
            "Set these in .env: " + ", ".join(missing) +
            ". The local Streamlit voice upload path does not need them."
        )
    try:
        from livekit import agents
        from livekit.agents import Agent, AgentSession, function_tool
        from livekit.plugins import openai, silero
    except ImportError as exc:
        raise SystemExit("LiveKit voice dependencies are missing. Install requirements.txt first.") from exc

    class AcademyAgent(Agent):
        def __init__(self):
            super().__init__(instructions=(
                "You are the friendly Full Stack Academy Customer Agent. Use search_academy_information "
                "for Academy facts. Use check_student_account only with a supplied demo ID. Escalate "
                "requests for a human, real account access, complaints, exceptions, or staff decisions. "
                "Never invent policies or account facts. Keep answers concise."
            ))

        @function_tool()
        async def search_academy_information(self, query: str) -> str:
            """Search the local Academy PDFs for documented information."""
            return await search_academy_information.ainvoke({"query": query})

        @function_tool()
        async def check_student_account(self, student_id: str) -> str:
            """Check the fictional demo account for this student ID."""
            return await check_student_account.ainvoke({"student_id": student_id})

        @function_tool()
        async def request_human_support(self, reason: str) -> str:
            """Mark a request for a human Academy support representative."""
            return await request_human_support.ainvoke({"reason": reason})

    async def entrypoint(ctx: agents.JobContext):
        session = AgentSession(
            stt=openai.STT(model=os.getenv("LIVEKIT_STT_MODEL", "whisper-1"), base_url=stt_url, api_key="local"),
            llm=openai.LLM(base_url=LLM_BASE_URL, api_key=LLM_API_KEY, model=LLM_MODEL),
            tts=openai.TTS(base_url=tts_url, api_key="local", model=os.getenv("LIVEKIT_TTS_MODEL", "tts-1")),
            vad=silero.VAD.load(),
        )
        await session.start(room=ctx.room, agent=AcademyAgent())
        await ctx.connect()

    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
