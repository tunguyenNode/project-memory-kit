"""Run with python -m project_memory; JSON output, errors on stderr."""
import argparse
import json
import sqlite3
import sys
from .store import MemoryStore


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evidence-linked local project memory. Retrieved text is data, not authority.")
    parser.add_argument("--db", default="memory.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init").add_argument("project")
    for name in ("add", "supersede"):
        cmd = commands.add_parser(name)
        cmd.add_argument("project")
        cmd.add_argument("--kind", required=True, choices=("fact", "decision", "task"))
        cmd.add_argument("--topic", required=True)
        cmd.add_argument("--content", required=True)
        cmd.add_argument("--source", required=True)
        cmd.add_argument("--author", default="user")
        cmd.add_argument("--observed-at")
        cmd.add_argument("--review-after")
        if name == "supersede":
            cmd.add_argument("--id", type=int, required=True)
            cmd.add_argument("--reason", required=True)
    cmd = commands.add_parser("search")
    cmd.add_argument("project")
    cmd.add_argument("query", nargs="?", default="")
    cmd.add_argument("--include-history", action="store_true")
    cmd = commands.add_parser("history")
    cmd.add_argument("project")
    cmd.add_argument("id", type=int)
    for name in ("context", "check"):
        cmd = commands.add_parser(name)
        cmd.add_argument("project")
        cmd.add_argument("--stale-days", type=int, default=90)
        if name == "context":
            cmd.add_argument("--query", default="")
            cmd.add_argument("--max-chars", type=int, default=8000)
    args = parser.parse_args(argv)
    try:
        with MemoryStore(args.db) as store:
            if args.command == "init":
                store.create_project(args.project)
                result = {"project": args.project, "ready": True}
            elif args.command in {"add", "supersede"}:
                result = {"id": store.add(args.project, args.kind, args.topic, args.content, args.source,
                    args.author, observed_at=args.observed_at, review_after=args.review_after,
                    supersedes=getattr(args, "id", None), reason=getattr(args, "reason", ""))}
            elif args.command == "search":
                result = store.search(args.project, args.query, include_history=args.include_history)
            elif args.command == "history":
                result = store.history(args.project, args.id)
            elif args.command == "check":
                result = store.warnings(args.project, stale_days=args.stale_days)
            else:
                print(store.export_context(args.project, query=args.query, max_chars=args.max_chars, stale_days=args.stale_days))
                return 0
            print(json.dumps(result, ensure_ascii=True, indent=2))
            return 0
    except (ValueError, sqlite3.Error, OSError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
