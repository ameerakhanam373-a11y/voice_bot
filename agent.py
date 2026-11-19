"""OpenAI-compatible local LLM orchestration with explicit, auditable tools."""
import json
import requests
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from tools import TOOL_BY_NAME

SYSTEM_PROMPT = """You are the friendly Full Stack Academy Customer Agent.
Help prospective and current students with programs, curriculum, admissions, eligibility, schedules, tuition, payment plans, enrollment, student support, and basic learning-platform questions.
For every question about Academy programs, admissions, tuition, schedules, or support, call search_academy_information before answering. If its excerpts contain the answer, answer from those excerpts and do not escalate. Escalate only when the requested detail is missing, the search index is unavailable, or the user asks for a human.
Use check_student_account only for a mock account question when the user provides a student ID.
Use request_human_support when the user asks for a human, an issue needs unavailable access, or a complaint, exception, or staff decision is involved.
Never invent Academy facts, account information, policies, or outcomes. The included documents are fictional demo material; describe their claims as demo policy when useful.
Keep replies concise and natural. Ask one clarification at a time. Do not promise admission, aid, jobs, refunds, credits, or exceptions. Do not reveal internal reasoning or tool implementation."""

TOOL_SPECS = [
    {"type": "function", "function": {"name": "search_academy_information", "description": "Search Academy documents for factual answers.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "check_student_account", "description": "Read mock account data by student ID.", "parameters": {"type": "object", "properties": {"student_id": {"type": "string"}}, "required": ["student_id"]}}},
    {"type": "function", "function": {"name": "request_human_support", "description": "Request follow-up from an Academy representative.", "parameters": {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"]}}},
]


class AgentError(RuntimeError):
    pass


def _chat(messages, use_tools=True):
    payload = {"model": LLM_MODEL, "messages": messages, "temperature": 0.3}
    if use_tools:
        payload["tools"] = TOOL_SPECS
        payload["tool_choice"] = "auto"
    try:
        response = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0
        if status in {401, 403}:
            detail = "The model API rejected the key. Check LLM_API_KEY in your .env file."
        elif status == 429:
            detail = "The model API rate limit or usage quota was reached. Check your provider dashboard and try later."
        elif status == 404:
            detail = "The model ID or API endpoint was not found. Check LLM_MODEL and LLM_BASE_URL in .env."
        else:
            detail = f"The model API returned HTTP {status}. Check the provider status and .env settings."
        raise AgentError(detail) from exc
    except requests.RequestException as exc:
        raise AgentError(
            f"Could not connect to the model endpoint at {LLM_BASE_URL}. "
            "Check your internet connection or local model server."
        ) from exc
    except (KeyError, ValueError) as exc:
        raise AgentError("The local model returned an unexpected response. Check that the selected model supports chat completions.") from exc


def answer_question(question: str, history=None) -> dict:
    """Return answer, safe tool activity, and retrieved source chunks."""
    if not question or not question.strip():
        return {"answer": "Please enter a question so I can help.", "tools": [], "sources": []}
    history = history or []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": question.strip()})
    used, sources = [], []
    try:
        for _ in range(4):
            message = _chat(messages)
            calls = message.get("tool_calls") or []
            if not calls:
                return {"answer": (message.get("content") or "I’m sorry, I couldn’t form a reply. Please try again.").strip(), "tools": used, "sources": sources}
            messages.append(message)
            for call in calls:
                name = call.get("function", {}).get("name", "")
                try:
                    args = json.loads(call.get("function", {}).get("arguments") or "{}")
                    tool_obj = TOOL_BY_NAME[name]
                    output = tool_obj.invoke(args)
                    used.append({"name": name, "status": "completed"})
                    if name == "search_academy_information":
                        from rag import search_documents
                        sources = search_documents(args.get("query", ""), limit=4)
                except Exception as exc:
                    output = f"That support tool is temporarily unavailable: {exc}"
                    used.append({"name": name or "unknown tool", "status": "unavailable"})
                messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": str(output)})
        return {"answer": "I’m having trouble completing that request. Please try again or ask for a support representative.", "tools": used, "sources": sources}
    except AgentError:
        raise
