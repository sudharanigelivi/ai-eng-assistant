import argparse
import json
import sys

from .engine import analyze
from .render import to_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m planner",
        description="Turn a software requirement into a structured, engineer-led plan.",
    )
    parser.add_argument("requirement", nargs="?", help="Requirement text (or use --file / stdin)")
    parser.add_argument("--file", help="Read the requirement from a file")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    args = parser.parse_args(argv)

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    elif args.requirement:
        text = args.requirement
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.error("provide a requirement, --file, or pipe text on stdin")

    try:
        plan = analyze(text)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(plan.to_dict(), indent=2) if args.format == "json" else to_markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
