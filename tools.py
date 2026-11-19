"""Safe, local tools available to the academy agent."""
from langchain_core.tools import tool
from rag import search_documents

MOCK_STUDENTS = {
    "FSA1001": {
        "name": "Ahmed",
        "outstanding_balance": 499,
        "program": "Full Stack Web Development",
        "enrollment_status": "Enrolled",
    }
}


@tool
def search_academy_information(query: str) -> str:
    """Search Academy documents for programs, policies, tuition, or support."""
    try:
        matches = search_documents(query, limit=4)
    except Exception:
        return "The local Academy search index is unavailable. Run document ingestion and try again."
    if not matches:
        return "I could not find that information in the Academy documents. Please ask a representative to confirm."
    return "\n\n".join(f"[{m['source']}, page {m['page']}] {m['text']}" for m in matches)


@tool
def check_student_account(student_id: str) -> str:
    """Read mock enrollment or balance data for the provided demo student ID."""
    student = MOCK_STUDENTS.get(student_id.strip().upper())
    if not student:
        return "I could not find a matching demo account. Please check the ID or contact student support."
    return (
        f"Mock account for {student['name']}: {student['enrollment_status']} in "
        f"{student['program']}. Outstanding demo balance: ${student['outstanding_balance']}."
    )


@tool
def request_human_support(reason: str) -> str:
    """Mark a request for follow-up by a human Academy representative."""
    safe_reason = (reason or "General support request").strip()[:240]
    return f"Your request has been marked for a Full Stack Academy support representative. Reason: {safe_reason}"


TOOL_BY_NAME = {t.name: t for t in (search_academy_information, check_student_account, request_human_support)}
