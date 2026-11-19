"""Run a text conversation in the terminal, or launch the optional LiveKit worker."""
import sys
from agent import AgentError, answer_question


def console() -> None:
    print("\nFULL STACK ACADEMY  /  CUSTOMER DESK")
    print("Local AI demo • Type 'quit' to leave\n")
    history = []
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break
        try:
            result = answer_question(question, history)
            print(f"\nAcademy AI: {result['answer']}\n")
            history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": result["answer"]}])
        except AgentError as exc:
            print(f"\nLocal model unavailable: {exc}\n")


def main() -> None:
    if len(sys.argv) == 1 or sys.argv[1] == "console":
        console()
    elif sys.argv[1] in {"dev", "start"}:
        from livekit_voice import run_worker
        run_worker()
    else:
        print("Usage: python main.py [console|dev]")


if __name__ == "__main__":
    main()
