"""Create fictional one-page starter PDFs using only Python's standard library."""
from pathlib import Path
import textwrap

DOCS_DIR = Path(__file__).resolve().parent / "docs"

CONTENT = {
    "programs.pdf": ("Programs and Learning Paths", [
        ("Web Development Foundations", "A fictional 12-week beginner path covering HTML, CSS, JavaScript fundamentals, Git, and portfolio exercises. No coding experience is assumed. Confirm current delivery dates with an Academy representative."),
        ("Full Stack Web Development", "A fictional 24-week program covering front-end development, APIs, databases, testing, and deployment. It is intended for learners with basic computer confidence; the demo guide does not guarantee a job or credential."),
        ("Learning format", "This demo describes guided online lessons, weekly practice, and optional office hours. Actual schedules, curriculum, instructor availability, and outcomes must be confirmed with the provider."),
    ]),
    "admissions.pdf": ("Admissions and Enrollment", [
        ("Demo application steps", "For this fictional example, prospective learners complete an interest form, speak with an advisor, review course expectations, and receive enrollment instructions. These are illustrative steps, not a real policy."),
        ("Eligibility", "The fictional beginner pathway has no coding prerequisite. Learners need reliable internet, a computer that can run a modern browser, and time for regular practice. Specific eligibility decisions require staff review."),
        ("Getting ready", "Check your device, use an email account you can access, and review the program outline. Do not submit sensitive personal information through this demo."),
    ]),
    "tuition.pdf": ("Tuition and Payment Guide", [
        ("Demo pricing", "All prices in this sample are fictional. A demo tuition figure of $2,400 is used only to show retrieval. It is not an offer, quote, invoice, or statement of current Academy pricing."),
        ("Illustrative payment options", "The example mentions paying in full or requesting a monthly schedule. Availability, fees, interest, eligibility, refunds, aid, and terms are undefined. Ask an authorized representative for current written terms."),
        ("Account questions", "This project contains one mock student record for software demonstration. It is not connected to billing or student records. Never enter a real student ID or payment information."),
    ]),
    "student_support.pdf": ("Student Support and Platform Help", [
        ("Portal sign-in checks", "Confirm the email address, check for an invitation or password-reset message, and try a current browser. Avoid sharing passwords or verification codes in chat."),
        ("Troubleshooting", "Try refreshing, temporarily disabling a browser extension, and checking the network. If the issue continues, note the time, browser, device, and error message, then contact a human representative."),
        ("When to escalate", "Escalate account access, payment, privacy, complaints, exceptions, and issues that may expose personal information. The demo cannot open real accounts or change records."),
    ]),
}


def make_pdf(title: str, sections: list[tuple[str, str]]) -> bytes:
    lines = ["FULL STACK ACADEMY / CUSTOMER DESK", title, "STARTER SOURCE DOCUMENT - FICTIONAL DEMO CONTENT", ""]
    for heading, body in sections:
        lines += [heading, *textwrap.wrap(body, width=86), ""]
    lines += textwrap.wrap("Replace this starter PDF with approved Academy material before real customer support.", width=86)
    commands = ["BT", "/F1 10 Tf", "50 748 Td", "14 TL"]
    for i, line in enumerate(lines):
        size = 19 if i == 1 else (8 if i == 2 else (11 if line and line == line.upper() else 10))
        if i:
            commands.append("T*")
        commands.append(f"/F1 {size} Tf")
        safe = line.encode("cp1252", errors="replace").decode("cp1252").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        commands.append(f"({safe}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("cp1252", errors="replace")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(out)


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, (title, sections) in CONTENT.items():
        (DOCS_DIR / filename).write_bytes(make_pdf(title, sections))
    print(f"Created {len(CONTENT)} fictional starter PDFs in {DOCS_DIR}")


if __name__ == "__main__":
    main()
