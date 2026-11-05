"""Save the project API key interactively without echoing it."""
import getpass
import os
from pathlib import Path
import sys


def main():
    if not sys.stdin.isatty():
        raise SystemExit("Run this script in your interactive SSH terminal.")
    target = Path(__file__).resolve().parent / ".env"
    if target.exists():
        raise SystemExit("An .env file already exists; nothing was overwritten.")
    key = getpass.getpass("OpenAI API key (hidden): ").strip()
    if not key or "\n" in key or "\r" in key:
        raise SystemExit("No valid single-line key entered; nothing was saved.")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write("OPENAI_API_KEY=" + key + "\n")
    print("Key saved securely. Its value was not displayed.")


if __name__ == "__main__":
    main()
